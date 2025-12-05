from typing import Optional
from sqlmodel import SQLModel, Field

class PedidoBase(SQLModel):
    producto_id: int
    cantidad: int
    estado: str = Field(default="Pendiente")

class Pedido(PedidoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class PedidoCreate(PedidoBase):
    pass