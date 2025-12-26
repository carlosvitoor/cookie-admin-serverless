import boto3
import os
import logging

logger = logging.getLogger()

class Database:
    _instance = None
    _table_resource = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Inicializa o recurso do DynamoDB apenas uma vez.
        """
        table_name = os.environ.get('TABLE_NAME')
        if not table_name:
            logger.error("Variavel de ambiente TABLE_NAME nao definida.")
            raise RuntimeError("Configuração de tabela ausente.")

        # O boto3.resource é mais alto nível que o client
        dynamodb = boto3.resource('dynamodb')
        self._table_resource = dynamodb.Table(table_name)
        logger.info(f"Conexão com DynamoDB estabelecida na tabela: {table_name}")

    @property
    def table(self):
        return self._table_resource

# Instância global para ser importada pelos repositórios
db_instance = Database()