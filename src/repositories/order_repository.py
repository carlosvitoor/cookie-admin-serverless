from boto3.dynamodb.conditions import Attr  # <--- Adicionar este import
from .base_repository import DynamoDBRepository
from decimal import Decimal

class OrderRepository(DynamoDBRepository):
    def save(self, order_dict: dict):
        self.table.put_item(Item=order_dict)

    def get_by_id(self, order_id: str):
        return self.table.get_item(Key={'id': order_id}).get('Item')

    def list_open_orders(self):
        """
        Retorna todos os pedidos que NÃO estão concluídos ou extraviados.
        """
        # Scan filtrando tudo que ainda está "em aberto"
        response = self.table.scan(
            FilterExpression=Attr('status').ne('CONCLUIDO') & Attr('status').ne('EXTRAVIADO')
        )
        return response.get('Items', [])
    # -------------------------------

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

    def update_status(self, pedido_id: str, novo_status: str, historico_entry: dict, data_conclusao: str = None):
        # Prepara update expression
        update_expr = "SET #st = :st, historico = list_append(if_not_exists(historico, :empty_list), :entry)"
        attr_values = {
            ':st': novo_status,
            ':entry': [historico_entry],
            ':empty_list': []
        }

        # Se houver data de conclusão, adiciona ao update
        if data_conclusao:
            update_expr += ", data_conclusao = :dc"
            attr_values[':dc'] = data_conclusao

        self.table.update_item(
            Key={'id': pedido_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues=attr_values
        )

    def register_occurrence(self, pedido_id: str, ocorrencia_dict: dict):
        self.table.update_item(
            Key={'id': pedido_id},
            UpdateExpression="SET #st = :st, ocorrencia = :oc, historico = list_append(if_not_exists(historico, :empty_list), :hist_entry)",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':st': 'EXTRAVIADO',
                ':oc': ocorrencia_dict,
                ':hist_entry': [{
                    "status_anterior": "EM_ROTA",
                    "novo_status": "EXTRAVIADO",
                    "data": ocorrencia_dict['data'],
                    "motivo": ocorrencia_dict['descricao']
                }],
                ':empty_list': []
            }
        )