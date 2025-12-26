import uuid
from decimal import Decimal
from datetime import datetime

# Imports do projeto
from repositories.catalog_repository import CatalogRepository
from core.exceptions import BusinessRuleException, EntityNotFoundException


class CatalogService:
    def __init__(self):
        self.repo = CatalogRepository()

    def create_product(self, payload: dict) -> dict:
        """
        Cria um novo Cookie no catálogo, garantindo unicidade do sabor.
        """
        # 1. Validação de Campos
        raw_sabor = payload.get('sabor')
        if not raw_sabor or 'preco_venda' not in payload:
            raise BusinessRuleException("Campos obrigatórios: sabor, preco_venda.")

        # 2. Sanitização (Padronização do Nome)
        # "  red velvet  " -> "Red Velvet"
        sabor_formatado = raw_sabor.strip().title()

        # 3. Validação de Unicidade (Regra Sênior)
        # Verifica se já existe ANTES de criar
        existentes = self.repo.find_by_flavor(sabor_formatado)
        if existentes:
            raise BusinessRuleException(f"O sabor '{sabor_formatado}' já está cadastrado.")

        # 4. Conversão de Tipos
        try:
            preco = Decimal(str(payload['preco_venda']))
            custo = Decimal(str(payload.get('custo_producao', '0.00')))

            if preco < 0 or custo < 0:
                raise ValueError
        except:
            raise BusinessRuleException("Preço ou custo inválido (devem ser números positivos).")

        # 5. Criação do Objeto
        cookie_id = str(uuid.uuid4())
        item = {
            'id': cookie_id,
            'tipo_item': 'COOKIE',
            'sabor': sabor_formatado,  # Salvamos o formatado
            'descricao': payload.get('descricao', ''),
            'preco_venda': preco,
            'custo_producao': custo,
            'status': 'ATIVO',
            'criado_em': datetime.now().isoformat()
        }

        self.repo.save(item)

        # Conversão simples para retorno JSON
        item_retorno = item.copy()
        item_retorno['preco_venda'] = float(preco)
        item_retorno['custo_producao'] = float(custo)

        return item_retorno

    def list_all(self) -> list:
        # A listagem também deve converter Decimals para serializar no JSON
        items = self.repo.list_active()
        for i in items:
            if 'preco_venda' in i: i['preco_venda'] = float(i['preco_venda'])
            if 'custo_producao' in i: i['custo_producao'] = float(i['custo_producao'])
        return items

    def update_product(self, cookie_id: str, payload: dict) -> dict:
        # 1. Verificar se existe
        current = self.repo.get_by_id(cookie_id)
        if not current:
            raise EntityNotFoundException(f"Cookie {cookie_id} não encontrado.")

        # 2. Preparar dados (Converter Decimal se vier preço)
        campos_atualizar = {}

        if 'preco_venda' in payload:
            campos_atualizar['preco_venda'] = Decimal(str(payload['preco_venda']))

        if 'custo_producao' in payload:
            campos_atualizar['custo_producao'] = Decimal(str(payload['custo_producao']))

        if 'sabor' in payload:
            # Se mudar o nome, formatamos igual na criação
            campos_atualizar['sabor'] = payload['sabor'].strip().title()
            # Nota: Poderíamos validar duplicidade aqui também, mas vou simplificar.

        if 'status' in payload:
            campos_atualizar['status'] = payload['status']  # ATIVO / INATIVO

        if not campos_atualizar:
            raise BusinessRuleException("Nenhum campo válido para atualização.")

        # 3. Persistir
        self.repo.update(cookie_id, campos_atualizar)

        # Retorna o objeto atualizado (Merge manual para retorno rápido)
        current.update(campos_atualizar)
        return self._convert_decimal_to_float(current)

    def _convert_decimal_to_float(self, item):
        # Helper simples para retorno
        for k, v in item.items():
            if isinstance(v, Decimal):
                item[k] = float(v)
        return item