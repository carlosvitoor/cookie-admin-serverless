class DomainException(Exception):
    """Classe base para erros de negócio."""
    pass

class EntityNotFoundException(DomainException):
    """Quando um ID (Cookie, Pedido) não é encontrado."""
    pass

class BusinessRuleException(DomainException):
    """Quando uma regra de negócio é violada (ex: preço negativo, estoque insuficiente)."""
    pass

class InfrastructureException(Exception):
    """Erros técnicos (banco fora do ar, erro de conexão)."""
    pass