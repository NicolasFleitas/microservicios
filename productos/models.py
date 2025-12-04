from typing import Optional
from sqlmodel import Field, SQLModel

class Producto(SQLModel, table=True):
    # 'table=True' le dice que esto va a la base de datos.
    # Si fuera solo para validar datos, sería table=False (o por defecto).

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    descripcion: str
    precio: float
    stock: int