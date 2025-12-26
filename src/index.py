import json
import logging
import os
from decimal import Decimal

# Importando Exceções e Serviços
from core.exceptions import BusinessRuleException, EntityNotFoundException
from services.catalog_service import CatalogService
from services.order_service import OrderService
from services.logistics_service import LogisticsService

# Setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Injeção de Dependências
catalog_service = CatalogService()
order_service = OrderService()
logistics_service = LogisticsService()

# Lê a origem permitida (injetada pelo stack.py) ou usa '*' como fallback
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')


def handler(event, context):
    """
    Controller: Recebe HTTP -> Chama Service -> Devolve HTTP
    """
    method = event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('rawPath', '/')

    # 1. Tratamento de Pre-flight (Browser pergunta: Posso chamar?)
    if method == 'OPTIONS':
        return response(200, "")

    try:
        # ROTA: /cookies (Catalog)
        if path == '/cookies':
            if method == 'GET':
                result = catalog_service.list_all()
                return response(200, result)

            elif method == 'POST':
                body = parse_body(event)
                result = catalog_service.create_product(body)
                return response(201, result)

        # ROTA: /orders (Sales)
        elif path == '/orders':
            if method == 'POST':
                body = parse_body(event)
                result = order_service.create_order(body)
                return response(201, result)

        # ROTA: /logistics/routes (Delivery)
        elif path == '/logistics/routes' and method == 'POST':
            body = parse_body(event)
            result = logistics_service.create_route(
                body.get('motoboy_nome'),
                body.get('custo_total'),
                body.get('pedidos_ids')
            )
            return response(200, result)

        # ROTA: /cookies/{id} (PUT para edição)
        elif path.startswith('/cookies/') and method == 'PUT':
            cookie_id = path.split('/')[-1]
            body = parse_body(event)
            result = catalog_service.update_product(cookie_id, body)
            return response(200, result)

        # ROTA: /orders/{id}/status (PATCH para status)
        elif path.startswith('/orders/') and path.endswith('/status') and method == 'PATCH':
            parts = path.split('/')  # ['', 'orders', '123', 'status']
            if len(parts) < 3: raise ValueError("ID inválido")

            pedido_id = parts[2]
            body = parse_body(event)
            novo_status = body.get('status')

            if not novo_status:
                raise ValueError("Campo 'status' obrigatório")

            result = order_service.update_order_status(pedido_id, novo_status)
            return response(200, result)

        # ROTA: /orders/{id}/loss (Registrar Extravio)
        elif path.startswith('/orders/') and path.endswith('/loss') and method == 'POST':
            parts = path.split('/')
            if len(parts) < 3: raise ValueError("ID inválido")

            pedido_id = parts[2]
            body = parse_body(event)
            motivo = body.get('motivo')

            if not motivo:
                raise BusinessRuleException("É obrigatório informar o motivo.")

            result = order_service.register_order_loss(pedido_id, motivo)
            return response(200, result)

        return response(404, {'error': 'Rota não encontrada'})

    # Tratamento de Erros Personalizado
    except EntityNotFoundException as e:
        return response(404, {'error': str(e)})
    except BusinessRuleException as e:
        return response(400, {'error': str(e)})
    except ValueError as e:
        return response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Erro Crítico: {e}", exc_info=True)
        return response(500, {'error': 'Erro interno do servidor'})


def parse_body(event):
    """Helper para evitar crash se o body vier vazio ou inválido"""
    try:
        return json.loads(event.get('body', '{}'))
    except:
        raise ValueError("O corpo da requisição não é um JSON válido.")


def response(status, body):
    """
    Gera a resposta HTTP com os headers de CORS obrigatórios.
    """
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            # AQUI ESTAVA FALTANDO:
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,PATCH"
        },
        "body": json.dumps(body, default=str)
    }