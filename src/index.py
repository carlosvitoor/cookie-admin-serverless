import json
import logging
import os
from decimal import Decimal

from core.exceptions import BusinessRuleException, EntityNotFoundException
from services.catalog_service import CatalogService
from services.order_service import OrderService
from services.logistics_service import LogisticsService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

catalog_service = CatalogService()
order_service = OrderService()
logistics_service = LogisticsService()

# Lê a origem permitida da variável de ambiente (injetada pelo stack.py)
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')

def handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('rawPath', '/')

    # Tratamento de Pre-flight (OPTIONS)
    if method == 'OPTIONS':
        return response(200, "")

    try:
        # ROTA: /cookies
        if path == '/cookies':
            if method == 'GET':
                result = catalog_service.list_all()
                return response(200, result)
            elif method == 'POST':
                body = json.loads(event.get('body', '{}'))
                result = catalog_service.create_product(body)
                return response(201, result)

        # ROTA: /orders
        elif path == '/orders':
            if method == 'POST':
                body = json.loads(event.get('body', '{}'))
                result = order_service.create_order(body)
                return response(201, result)

        # ROTA: /logistics/routes
        elif path == '/logistics/routes' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            result = logistics_service.create_route(
                body.get('motoboy_nome'),
                body.get('custo_total'),
                body.get('pedidos_ids')
            )
            return response(200, result)

        # ROTA: /cookies/{id} (PUT)
        elif path.startswith('/cookies/') and method == 'PUT':
            cookie_id = path.split('/')[-1]
            body = json.loads(event.get('body', '{}'))
            result = catalog_service.update_product(cookie_id, body)
            return response(200, result)

        # ROTA: /orders/{id}/status (PATCH)
        elif path.startswith('/orders/') and path.endswith('/status') and method == 'PATCH':
            parts = path.split('/')
            if len(parts) >= 3:
                pedido_id = parts[2]
                body = json.loads(event.get('body', '{}'))
                novo_status = body.get('status')
                if not novo_status:
                    raise ValueError("Campo 'status' obrigatório")
                result = order_service.update_order_status(pedido_id, novo_status)
                return response(200, result)

        # ROTA: /orders/{id}/loss (POST)
        elif path.startswith('/orders/') and path.endswith('/loss') and method == 'POST':
            parts = path.split('/')
            if len(parts) >= 3:
                pedido_id = parts[2]
                body = json.loads(event.get('body', '{}'))
                motivo = body.get('motivo')
                if not motivo:
                    raise BusinessRuleException("Motivo obrigatório")
                result = order_service.register_order_loss(pedido_id, motivo)
                return response(200, result)

        return response(404, {'error': 'Rota não encontrada'})

    except EntityNotFoundException as e:
        return response(404, {'error': str(e)})
    except BusinessRuleException as e:
        return response(400, {'error': str(e)})
    except ValueError as e:
        return response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Erro Crítico: {e}", exc_info=True)
        return response(500, {'error': 'Erro interno'})

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN, # <--- AQUI ESTÁ A MÁGICA
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,PATCH"
        },
        "body": json.dumps(body, default=str)
    }