import uuid
import json
from decimal import Decimal
from datetime import datetime

# Imports dos Modelos e Repositórios
from models import PedidoModel, ItemPedidoSnapshot, StatusPedido
from repositories.catalog_repository import CatalogRepository
from repositories.order_repository import OrderRepository
from core.exceptions import BusinessRuleException, EntityNotFoundException


class OrderService:
    def __init__(self):
        # Injeção das dependências de banco de dados
        self.catalog_repo = CatalogRepository()
        self.order_repo = OrderRepository()

    def create_order(self, payload: dict) -> dict:
        """
        Cria um novo pedido aplicando as Regras de Negócio:
        1. Validação de Itens Duplicados (Input Integrity).
        2. Snapshot de Preços e Custos (Financial Integrity).
        """
        itens_entrada = payload.get('itens', [])

        # REGRA 1: Pedido não pode ser vazio
        if not itens_entrada:
            raise BusinessRuleException("O pedido deve conter pelo menos um item.")

        itens_snapshot = []
        total_venda = Decimal('0.00')

        # REGRA 2: Validação de Duplicidade (O Set rastrea quem já vimos)
        ids_processados = set()

        for item_input in itens_entrada:
            cookie_id = item_input.get('cookie_id')

            # Validação básica de tipo e valor
            try:
                qtd = int(item_input.get('qtd', 0))
            except ValueError:
                raise BusinessRuleException(f"Quantidade inválida para o item {cookie_id}.")

            if qtd <= 0:
                raise BusinessRuleException(f"A quantidade deve ser maior que zero para o item {cookie_id}.")

            # --- AQUI ESTÁ A PROTEÇÃO CONTRA DUPLICATAS ---
            if cookie_id in ids_processados:
                raise BusinessRuleException(
                    f"Item duplicado no pedido: {cookie_id}. "
                    "Não envie o mesmo produto em linhas separadas. "
                    "Consolide a quantidade em um único item."
                )

            # Marca ID como processado
            ids_processados.add(cookie_id)

            # --- LÓGICA DE SNAPSHOT (Congelamento de Preço) ---
            # Buscamos o dado original no catálogo
            cookie_data = self.catalog_repo.get_by_id(cookie_id)

            if not cookie_data:
                raise EntityNotFoundException(f"Cookie {cookie_id} não encontrado no catálogo.")

            # Convertendo para Decimal (Dinheiro)
            preco_atual = Decimal(str(cookie_data.get('preco_venda', '0.00')))
            custo_atual = Decimal(str(cookie_data.get('custo_producao', '0.00')))

            # Criamos o objeto Item imutável
            snapshot = ItemPedidoSnapshot(
                cookie_id=cookie_data['id'],
                sabor=cookie_data['sabor'],
                qtd=qtd,
                preco_venda_unitario=preco_atual,
                custo_producao_unitario=custo_atual,  # Salvamos o CUSTO aqui para relatórios futuros
                subtotal_venda=preco_atual * qtd
            )

            itens_snapshot.append(snapshot)
            total_venda += snapshot.subtotal_venda

        # Montagem do Pedido Final
        pedido = PedidoModel(
            id=f"ord_{str(uuid.uuid4())[:8]}",
            cliente_nome=payload.get('cliente_nome', 'Cliente Balcão'),
            itens=itens_snapshot,
            valor_total_venda=total_venda,
            status=StatusPedido.RECEBIDO
        )

        # Preparação para o DynamoDB (Serialização)
        order_dict = json.loads(pedido.model_dump_json())

        # Helper recursivo: converte floats do JSON para Decimal do DynamoDB
        self._fix_decimals(order_dict)

        # Persistência
        self.order_repo.save(order_dict)

        return order_dict

    def _fix_decimals(self, obj):
        """
        Função auxiliar para converter tipos float (do JSON) para Decimal (do DynamoDB).
        O DynamoDB não aceita float nativo do Python por questões de precisão.
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, float):
                    obj[k] = Decimal(str(v))
                else:
                    self._fix_decimals(v)
        elif isinstance(obj, list):
            for item in obj:
                self._fix_decimals(item)
        return obj

    def update_order_status(self, pedido_id: str, novo_status: str):
        # 1. Validar se o status existe no Enum
        if novo_status not in StatusPedido.__members__:
            # Se o frontend mandar string solta, tentamos mapear ou barramos
            if novo_status not in [s.value for s in StatusPedido]:
                raise BusinessRuleException(f"Status inválido: {novo_status}")

        # 2. Buscar status atual (para auditoria)
        pedido = self.order_repo.get_by_id(pedido_id)
        if not pedido:
            raise EntityNotFoundException("Pedido não encontrado")

        status_anterior = pedido.get('status', 'DESCONHECIDO')

        # Se já estiver no status, não faz nada
        if status_anterior == novo_status:
            return {"message": "O pedido já está neste status."}

        # 3. Criar entrada de histórico
        entry = {
            "status_anterior": status_anterior,
            "novo_status": novo_status,
            "data_alteracao": datetime.now().isoformat()
        }

        # 4. Atualizar no banco
        self.order_repo.update_status(pedido_id, novo_status, entry)

        return {
            "id": pedido_id,
            "status_novo": novo_status,
            "historico_adicionado": entry
        }

    def register_order_loss(self, pedido_id: str, motivo: str) -> dict:
        """
        Calcula o prejuízo total (CMV + Logística) e registra o extravio.
        """
        # 1. Buscar o pedido para acessar os snapshots de custo
        pedido = self.order_repo.get_by_id(pedido_id)
        if not pedido:
            raise EntityNotFoundException("Pedido não encontrado.")

        if pedido.get('status') == 'EXTRAVIADO':
            raise BusinessRuleException("Este pedido já foi marcado como extraviado.")

        # 2. Calcular Prejuízo de Produtos (CMV Perdido)
        # Usamos o custo snapshotado no momento da criação
        prejuizo_produtos = Decimal('0.00')
        itens = pedido.get('itens', [])

        for item in itens:
            custo_unit = Decimal(str(item.get('custo_producao_unitario', '0')))
            qtd = Decimal(str(item.get('qtd', '0')))
            prejuizo_produtos += (custo_unit * qtd)

        # 3. Calcular Prejuízo Logístico (O que pagamos ao motoboy à toa)
        prejuizo_entrega = Decimal(str(pedido.get('custo_entrega_rateado', '0.00')))

        prejuizo_total = prejuizo_produtos + prejuizo_entrega

        # 4. Montar o Objeto de Ocorrência (Auditoria)
        ocorrencia = {
            "data": datetime.now().isoformat(),
            "tipo": "EXTRAVIO",
            "descricao": motivo,
            "responsavel_prejuizo": "LOJA",
            "calculo_financeiro": {
                "prejuizo_produtos": prejuizo_produtos,
                "prejuizo_entrega": prejuizo_entrega,
                "prejuizo_total": prejuizo_total
            }
        }

        # 5. Persistir (Convertendo Decimals para serialização do Dynamo se necessário,
        # mas como estamos passando via boto3 update_item, ele aceita Decimal,
        # exceto dentro de listas/mapas complexos as vezes, vamos converter pra garantir)

        # Hack rápido para converter Decimals do dict para passar pro Dynamo
        ocorrencia_dynamo = json.loads(json.dumps(ocorrencia, default=str), parse_float=Decimal)

        self.order_repo.register_occurrence(pedido_id, ocorrencia_dynamo)

        return {
            "message": "Extravio registrado com sucesso.",
            "pedido_id": pedido_id,
            "prejuizo_contabilizado": float(prejuizo_total)
        }