import json
import logging
import os
from decimal import Decimal

# Imports de Exceções
from core.exceptions import BusinessRuleException, EntityNotFoundException

# Importando os Serviços
from services.catalog_service import CatalogService
from services.order_service import OrderService
from services.logistics_service import LogisticsService

# Setup de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Singleton (Injeção de Dependências)
catalog_service = CatalogService()
order_service = OrderService()
logistics_service = LogisticsService()

# Configuração CORS (Lê de variável de ambiente ou usa * como fallback inseguro)
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')


def handler(event, context):
    """
    Router Principal (Controller)
    """
    method = event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('rawPath', '/')

    # Tratamento do Pre-flight (Browser pergunta: Posso?)
    if method == 'OPTIONS':
        return response(200, "")

    try:
        # --- ROTA: /cookies (Catálogo) ---
        if path == '/cookies':
            if method == 'GET':
                result = catalog_service.list_all()
                return response(200, result)

            elif method == 'POST':
                body = parse_body(event)
                result = catalog_service.create_product(body)
                return response(201, result)

        elif path.startswith('/cookies/') and method == 'PUT':
            # /cookies/{id}
            cookie_id = path.split('/')[-1]
            body = parse_body(event)
            result = catalog_service.update_product(cookie_id, body)
            return response(200, result)

        # --- ROTA: /orders (Pedidos) ---
        elif path == '/orders':
            if method == 'POST':
                body = parse_body(event)
                result = order_service.create_order(body)
                return response(201, result)

        # PATCH /orders/{id}/status
        elif path.startswith('/orders/') and path.endswith('/status') and method == 'PATCH':
            # parts: ['', 'orders', 'ord_123', 'status'] -> ID é indice 2
            parts = path.split('/')
            if len(parts) < 3:
                raise ValueError("ID do pedido não identificado na URL")

            pedido_id = parts[2]
            body = parse_body(event)

            if 'status' not in body:
                raise ValueError("Campo 'status' é obrigatório")

            result = order_service.update_order_status(pedido_id, body['status'])
            return response(200, result)

        # POST /orders/{id}/loss
        elif path.startswith('/orders/') and path.endswith('/loss') and method == 'POST':
            parts = path.split('/')
            if len(parts) < 3:
                raise ValueError("ID do pedido não identificado na URL")

            pedido_id = parts[2]
            body = parse_body(event)

            if 'motivo' not in body:
                raise BusinessRuleException("É obrigatório informar o motivo.")

            result = order_service.register_order_loss(pedido_id, body['motivo'])
            return response(200, result)

        # --- ROTA: /logistics (Entregas) ---
        elif path == '/logistics/routes' and method == 'POST':
            body = parse_body(event)
            result = logistics_service.create_route(
                body.get('motoboy_nome'),
                body.get('custo_total'),
                body.get('pedidos_ids')
            )
            return response(200, result)

        # Rota não encontrada
        return response(404, {'error': 'Rota não encontrada'})

    except EntityNotFoundException as e:
        logger.warning(f"Not Found: {str(e)}")
        return response(404, {'error': str(e)})

    except BusinessRuleException as e:
        logger.warning(f"Business Rule: {str(e)}")
        return response(400, {'error': str(e)})

    except ValueError as e:
        logger.warning(f"Bad Request: {str(e)}")
        return response(400, {'error': str(e)})

    except Exception as e:
        logger.error(f"Internal Error: {str(e)}", exc_info=True)
        return response(500, {'error': 'Erro interno do servidor'})


# --- Helpers ---

def parse_body(event):
    """Decodifica o body com segurança"""
    try:
        return json.loads(event.get('body', '{}'))
    except:
        raise ValueError("Body inválido (não é JSON)")


def response(status, body):
    """Gera a resposta HTTP com CORS injetado"""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,PATCH"
        },
        "body": json.dumps(body, default=str) if body is not None else ""
    }