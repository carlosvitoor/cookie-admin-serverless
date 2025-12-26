import uuid
from decimal import Decimal
from repositories.order_repository import OrderRepository


class LogisticsService:
    def __init__(self):
        # Repositório genérico, poderia ser um DeliveryRepository específico
        self.repo = OrderRepository()

    def create_route(self, motoboy_nome: str, custo_total: float, pedidos_ids: list):
        if not pedidos_ids:
            raise ValueError("Rota vazia")

        custo_total_dec = Decimal(str(custo_total))

        # REGRA DE NEGÓCIO: Rateio Simples
        rateio = (custo_total_dec / len(pedidos_ids)).quantize(Decimal("0.01"))
        entrega_id = f"ent_{str(uuid.uuid4())[:8]}"

        # 1. Persistir a Entrega (Simplificado: usando o mesmo repo por enquanto)
        entrega_dict = {
            'id': entrega_id,
            'tipo_item': 'ENTREGA',
            'custo_total': custo_total_dec,
            'motoboy': motoboy_nome
        }
        self.repo.save(entrega_dict)

        # 2. Atualizar Pedidos
        for pid in pedidos_ids:
            self.repo.update_logistics(pid, entrega_id, rateio)

        return {"entrega_id": entrega_id, "custo_por_pedido": rateio}