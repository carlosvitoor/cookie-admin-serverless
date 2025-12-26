from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum


class StatusPedido(str, Enum):
    RECEBIDO = "RECEBIDO"
    EM_PREPARO = "EM_PREPARO"
    EM_ROTA = "EM_ROTA"
    CONCLUIDO = "CONCLUIDO"
    EXTRAVIADO = "EXTRAVIADO"


class ItemPedidoSnapshot(BaseModel):
    cookie_id: str
    sabor: str
    qtd: int
    preco_venda_unitario: Decimal
    custo_producao_unitario: Decimal
    subtotal_venda: Decimal


class Ocorrencia(BaseModel):
    data: str = Field(default_factory=lambda: datetime.now().isoformat())
    tipo: str
    descricao: str
    responsavel_prejuizo: str = "LOJA"
    prejuizo_produtos: Decimal
    prejuizo_entrega: Decimal
    prejuizo_total: Decimal


class PedidoModel(BaseModel):
    id: Optional[str] = None
    tipo_item: str = "PEDIDO"
    cliente_nome: str
    itens: List[ItemPedidoSnapshot]

    valor_total_venda: Decimal

    # Logística
    entrega_id: Optional[str] = None
    custo_entrega_rateado: Optional[Decimal] = None

    status: StatusPedido = StatusPedido.RECEBIDO
    ocorrencia: Optional[Ocorrencia] = None

    criado_em: str = Field(default_factory=lambda: datetime.now().isoformat())

    # MUDANÇA: Apenas a data combinada, sem minutos calculados
    data_entrega: str  # Obrigatório (ISO Format)
    data_conclusao: Optional[str] = None