from typing import Optional
from sqlmodel import SQLModel, Field

class InventarioBase(SQLModel):
    cantidad: int
    producto_id: int

class Inventario(InventarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class InventarioCreate(InventarioBase):
    pass
