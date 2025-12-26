import boto3

from .base_repository import DynamoDBRepository
from botocore.exceptions import ClientError

class CatalogRepository(DynamoDBRepository):
    def get_by_id(self, cookie_id: str):
        resp = self.table.get_item(Key={'id': cookie_id})
        return resp.get('Item')

    def save(self, item: dict):
        self.table.put_item(Item=item)

    def list_active(self):
        # Aqui abstraimos a query do Dynamo
        return self.table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('tipo_item').eq('COOKIE')
        ).get('Items', [])