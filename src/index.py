import json
import logging
from decimal import Decimal

from core.exceptions import BusinessRuleException
# Importando os Serviços
from services.catalog_service import CatalogService
from services.order_service import OrderService
from services.logistics_service import LogisticsService

# Setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Singleton (Injeção de Dependências simples)
catalog_service = CatalogService()
order_service = OrderService()
logistics_service = LogisticsService()


def handler(event, context):
    """
    Controller: Recebe HTTP -> Chama Service -> Devolve HTTP
    """
    method = event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('rawPath', '/')

    try:
        # ROTA: /cookies (Catalog)
        if path == '/cookies':
            if method == 'GET':
                result = catalog_service.list_all()
                return response(200, result)

            elif method == 'POST':
                body = json.loads(event.get('body', '{}'))
                result = catalog_service.create_product(body)
                return response(201, result)

        # ROTA: /orders (Sales)
        elif path == '/orders':
            if method == 'POST':
                body = json.loads(event.get('body', '{}'))
                result = order_service.create_order(body)
                return response(201, result)

        # ROTA: /logistics/routes (Delivery)
        elif path == '/logistics/routes' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            result = logistics_service.create_route(
                body['motoboy_nome'],
                body['custo_total'],
                body['pedidos_ids']
            )
            return response(200, result)

        # ROTA: /cookies (PUT para edição)
        elif path.startswith('/cookies/') and method == 'PUT':
            # Extrair ID da URL: /cookies/123 -> 123
            cookie_id = path.split('/')[-1]
            body = json.loads(event.get('body', '{}'))
            result = catalog_service.update_product(cookie_id, body)
            return response(200, result)

        # ROTA: /orders (PATCH para status)
        elif path.startswith('/orders/') and method == 'PATCH':
            # Ex: PATCH /orders/ord_123/status
            parts = path.split('/')
            pedido_id = parts[2]  # assumindo /orders/{id}/status

            body = json.loads(event.get('body', '{}'))
            novo_status = body.get('status')

            if not novo_status:
                raise ValueError("Campo 'status' obrigatório")

            result = order_service.update_order_status(pedido_id, novo_status)
            return response(200, result)

        # ROTA: /orders/{id}/loss (Registrar Extravio/Perda)
        elif path.endswith('/loss') and method == 'POST':
            # Ex: POST /orders/ord_123/loss
            # path parts: ['', 'orders', 'ord_123', 'loss']
            parts = path.split('/')
            pedido_id = parts[2]

            body = json.loads(event.get('body', '{}'))
            motivo = body.get('motivo')

            if not motivo:
                raise BusinessRuleException("É obrigatório informar o motivo do extravio.")

            result = order_service.register_order_loss(pedido_id, motivo)
            return response(200, result)

        return response(404, {'error': 'Rota não encontrada'})

    except ValueError as e:
        return response(400, {'error': str(e)})  # Bad Request (Regra de Negocio)
    except Exception as e:
        logger.error(f"Erro Crítico: {e}", exc_info=True)
        return response(500, {'error': 'Erro interno'})


def response(status, body):
    # Serializador JSON customizado para Decimal omitido para brevidade
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }