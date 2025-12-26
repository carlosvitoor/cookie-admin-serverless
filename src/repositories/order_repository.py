from .base_repository import DynamoDBRepository
from decimal import Decimal

class OrderRepository(DynamoDBRepository):
    def save(self, order_dict: dict):
        self.table.put_item(Item=order_dict)

    def get_by_id(self, order_id: str):
        return self.table.get_item(Key={'id': order_id}).get('Item')

    def update_logistics(self, order_id: str, entrega_id: str, custo_rateado: Decimal):
        self.table.update_item(
            Key={'id': order_id},
            UpdateExpression="SET entrega_id=:e, custo_entrega_rateado=:c, #st=:s",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':e': entrega_id,
                ':c': custo_rateado,
                ':s': 'EM_ROTA'
            }
        )