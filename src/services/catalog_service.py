import uuid
import json
from decimal import Decimal
from datetime import datetime

# Imports do projeto
from repositories.catalog_repository import CatalogRepository
from core.exceptions import BusinessRuleException


class CatalogService:
    def __init__(self):
        self.repo = CatalogRepository()

    def create_product(self, payload: dict) -> dict:
        """
        Cria um novo Cookie no catálogo.
        """
        # Validação básica de entrada
        if 'sabor' not in payload or 'preco_venda' not in payload:
            raise BusinessRuleException("Campos obrigatórios: sabor, preco_venda.")

        cookie_id = str(uuid.uuid4())

        # Converte para Decimal para evitar erro no DynamoDB
        try:
            preco = Decimal(str(payload['preco_venda']))
            custo = Decimal(str(payload.get('custo_producao', '0.00')))
        except:
            raise BusinessRuleException("Preço ou custo inválido.")

        item = {
            'id': cookie_id,
            'tipo_item': 'COOKIE',
            'sabor': payload['sabor'],
            'descricao': payload.get('descricao', ''),
            'preco_venda': preco,
            'custo_producao': custo,
            'status': 'ATIVO',
            'criado_em': datetime.now().isoformat()
        }

        self.repo.save(item)

        # Retorna o dict, mas converte Decimal para float/str para serialização JSON se necessário no controller
        return item

    def list_all(self) -> list:
        """
        Retorna todos os cookies ativos.
        """
        return self.repo.list_active()