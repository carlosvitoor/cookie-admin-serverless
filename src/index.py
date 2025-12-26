import json
import logging
from decimal import Decimal

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