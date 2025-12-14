from typing import Optional
from sqlmodel import Field, SQLModel

# Clase Base: Contiene los campos comunes
class ProductoBase(SQLModel):
    nombre: str = Field(index=True, unique=True)
    descripcion: str
    precio: float

class Producto(ProductoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(ProductoBase):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
