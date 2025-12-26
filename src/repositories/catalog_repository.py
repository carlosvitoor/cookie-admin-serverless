from boto3.dynamodb.conditions import Attr
from .base_repository import DynamoDBRepository

class CatalogRepository(DynamoDBRepository):
    def get_by_id(self, cookie_id: str):
        resp = self.table.get_item(Key={'id': cookie_id})
        return resp.get('Item')

    def save(self, item: dict):
        self.table.put_item(Item=item)

    def list_active(self):
        return self.table.scan(
            FilterExpression=Attr('tipo_item').eq('COOKIE') & Attr('status').eq('ATIVO')
        ).get('Items', [])

    def find_by_flavor(self, sabor: str):
        """
        Busca um cookie pelo nome exato (case sensitive no banco,
        mas vamos tratar no service).
        """
        response = self.table.scan(
            FilterExpression=Attr('tipo_item').eq('COOKIE') & Attr('sabor').eq(sabor)
        )
        return response.get('Items', [])