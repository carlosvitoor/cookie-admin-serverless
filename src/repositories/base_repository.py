from core.database import db_instance

class DynamoDBRepository:
    def __init__(self):
        # Usa a instância singleton já inicializada
        self.table = db_instance.table