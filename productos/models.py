from typing import Optional
from sqlmodel import Field, SQLModel

# 1. Clase Base: Contiene los campos comunes
class ProductoBase(SQLModel):
    # 'table=True' le dice que esto va a la base de datos.
    # Si fuera solo para validar datos, sería table=False (o por defecto).

    nombre: str = Field(index=True)
    descripcion: str
    precio: float

# 2 Modelo para la Tabla (Hereda de Base): Agrega el ID
class Producto(ProductoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# 3. Modelo para Crear (Hereda de Base)
# No agrega nada nuevo, pero sirve para diferenciar que acá NO esperamos un ID.

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(ProductoBase):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
