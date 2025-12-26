import uuid
import json
from decimal import Decimal
from datetime import datetime
from models import PedidoModel, ItemPedidoSnapshot, StatusPedido
# Injeção de dependência "manual" via construtor
from repositories.catalog_repository import CatalogRepository
from repositories.order_repository import OrderRepository


class OrderService:
    def __init__(self):
        self.catalog_repo = CatalogRepository()
        self.order_repo = OrderRepository()

    def create_order(self, payload: dict) -> dict:
        itens_entrada = payload.get('itens', [])
        itens_snapshot = []
        total_venda = Decimal('0.00')

        # REGRA DE NEGÓCIO: Snapshot de Preços
        for item_input in itens_entrada:
            cookie_data = self.catalog_repo.get_by_id(item_input['cookie_id'])

            if not cookie_data:
                raise ValueError(f"Cookie {item_input['cookie_id']} não existe.")

            preco_atual = Decimal(str(cookie_data.get('preco_venda')))
            custo_atual = Decimal(str(cookie_data.get('custo_producao')))
            qtd = int(item_input['qtd'])

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

        # Criação do Modelo
        pedido = PedidoModel(
            id=f"ord_{str(uuid.uuid4())[:8]}",
            cliente_nome=payload.get('cliente_nome'),
            itens=itens_snapshot,
            valor_total_venda=total_venda
        )

        # Serialização e Persistência
        # (Assumindo que temos um helper de conversão aqui)
        order_dict = json.loads(pedido.model_dump_json())
        self._fix_decimals(order_dict)

        self.order_repo.save(order_dict)
        return order_dict

    def _fix_decimals(self, obj):
        # Helper method privado para tratar floats -> Decimal
        pass