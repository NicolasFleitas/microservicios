from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class InventarioBase(SQLModel):
    cantidad: int = Field(gt=0)
    producto_id: int = Field(unique=True)

class Inventario(InventarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class InventarioCreate(InventarioBase):
    pass

# Esquema simple solo para recibir cuánto restar
class InventarioUpdate(BaseModel):
    cantidad: int = Field(gt=0)
    tipo_movimiento: str
