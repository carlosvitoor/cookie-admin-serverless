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

    def update_status(self, pedido_id: str, novo_status: str, historico_entry: dict):
        """
        Atualiza o status E adiciona um item na lista de histórico (timeline).
        """
        self.table.update_item(
            Key={'id': pedido_id},
            UpdateExpression="SET #st = :st, historico = list_append(if_not_exists(historico, :empty_list), :entry)",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':st': novo_status,
                ':entry': [historico_entry],  # Tem que ser uma lista para o list_append funcionar
                ':empty_list': []
            }
        )

    def register_occurrence(self, pedido_id: str, ocorrencia_dict: dict):
        """
        Marca como extraviado e persiste os dados do prejuízo calculado.
        """
        self.table.update_item(
            Key={'id': pedido_id},
            UpdateExpression="SET #st = :st, ocorrencia = :oc, historico = list_append(if_not_exists(historico, :empty_list), :hist_entry)",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':st': 'EXTRAVIADO',
                ':oc': ocorrencia_dict,
                ':hist_entry': [{
                    "status_anterior": "EM_ROTA",  # Assumindo que estava na rua
                    "novo_status": "EXTRAVIADO",
                    "data": ocorrencia_dict['data'],
                    "motivo": ocorrencia_dict['descricao']
                }],
                ':empty_list': []
            }
        )