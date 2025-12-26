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
        self.catalog_repo = CatalogRepository()
        self.order_repo = OrderRepository()

    def list_active(self):
        items = self.order_repo.list_open_orders()
        return self._fix_decimals(items)

    def create_order(self, payload: dict) -> dict:
        itens_entrada = payload.get('itens', [])

        # MUDANÇA: Recebe a data combinada
        data_entrega_str = payload.get('data_entrega')

        if not data_entrega_str:
            raise BusinessRuleException("A Data de Entrega da encomenda é obrigatória.")

        if not itens_entrada:
            raise BusinessRuleException("A encomenda deve conter pelo menos um item.")

        itens_snapshot = []
        total_venda = Decimal('0.00')
        ids_processados = set()

        for item_input in itens_entrada:
            cookie_id = item_input.get('cookie_id')
            try:
                qtd = int(item_input.get('qtd', 0))
            except ValueError:
                raise BusinessRuleException(f"Quantidade inválida para o item {cookie_id}.")

            if qtd <= 0:
                raise BusinessRuleException(f"Quantidade deve ser maior que zero.")

            if cookie_id in ids_processados:
                raise BusinessRuleException(f"Item duplicado: {cookie_id}.")

            ids_processados.add(cookie_id)
            cookie_data = self.catalog_repo.get_by_id(cookie_id)

            if not cookie_data:
                raise EntityNotFoundException(f"Cookie {cookie_id} não encontrado.")

            preco_atual = Decimal(str(cookie_data.get('preco_venda', '0.00')))
            custo_atual = Decimal(str(cookie_data.get('custo_producao', '0.00')))

            snapshot = ItemPedidoSnapshot(
                cookie_id=cookie_data['id'],
                sabor=cookie_data['sabor'],
                qtd=qtd,
                preco_venda_unitario=preco_atual,
                custo_producao_unitario=custo_atual,
                subtotal_venda=preco_atual * qtd
            )
            itens_snapshot.append(snapshot)
            total_venda += snapshot.subtotal_venda

        # Montagem do Pedido
        pedido = PedidoModel(
            id=f"ord_{str(uuid.uuid4())[:8]}",
            cliente_nome=payload.get('cliente_nome', 'Cliente Online'),
            itens=itens_snapshot,
            valor_total_venda=total_venda,
            status=StatusPedido.RECEBIDO,
            data_entrega=data_entrega_str,  # Salva a data combinada
            criado_em=datetime.now().isoformat()
        )

        order_dict = json.loads(pedido.model_dump_json())
        self._fix_decimals(order_dict)
        self.order_repo.save(order_dict)

        return order_dict

    def _fix_decimals(self, obj):
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
        if novo_status not in StatusPedido.__members__:
            if novo_status not in [s.value for s in StatusPedido]:
                raise BusinessRuleException(f"Status inválido: {novo_status}")

        pedido = self.order_repo.get_by_id(pedido_id)
        if not pedido:
            raise EntityNotFoundException("Pedido não encontrado")

        status_anterior = pedido.get('status', 'DESCONHECIDO')

        if status_anterior == novo_status:
            return {"message": "O pedido já está neste status."}

        data_conclusao = None
        if novo_status == "CONCLUIDO":
            data_conclusao = datetime.now().isoformat()

        entry = {
            "status_anterior": status_anterior,
            "novo_status": novo_status,
            "data_alteracao": datetime.now().isoformat()
        }

        self.order_repo.update_status(pedido_id, novo_status, entry, data_conclusao)

        return {
            "id": pedido_id,
            "status_novo": novo_status,
            "concluido_em": data_conclusao
        }

    def register_order_loss(self, pedido_id: str, motivo: str) -> dict:
        pedido = self.order_repo.get_by_id(pedido_id)
        if not pedido:
            raise EntityNotFoundException("Pedido não encontrado.")

        if pedido.get('status') == 'EXTRAVIADO':
            raise BusinessRuleException("Já extraviado.")

        prejuizo_produtos = Decimal('0.00')
        itens = pedido.get('itens', [])

        for item in itens:
            custo_unit = Decimal(str(item.get('custo_producao_unitario', '0')))
            qtd = Decimal(str(item.get('qtd', '0')))
            prejuizo_produtos += (custo_unit * qtd)

        prejuizo_entrega = Decimal(str(pedido.get('custo_entrega_rateado', '0.00')))
        prejuizo_total = prejuizo_produtos + prejuizo_entrega

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

        ocorrencia_dynamo = json.loads(json.dumps(ocorrencia, default=str), parse_float=Decimal)
        self.order_repo.register_occurrence(pedido_id, ocorrencia_dynamo)

        return {
            "message": "Extravio registrado.",
            "pedido_id": pedido_id,
            "prejuizo_total": float(prejuizo_total)
        }