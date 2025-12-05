from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importación de modelos y la conexio
from inventario.database import init_db, get_session
from inventario.models import Inventario, InventarioCreate, InventarioUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos Inventario")
    await init_db()
    yield
    print("Cerrando la base de datos Inventario")

app = FastAPI(lifespan=lifespan)

@app.post("/inventario", response_model=Inventario)
async def crear_inventario(inventario_data: InventarioCreate, session: AsyncSession = Depends(get_session)):
   
    nuevo_inventario = Inventario.model_validate(inventario_data)

    session.add(nuevo_inventario)
    await session.commit()
    await session.refresh(nuevo_inventario)

    return nuevo_inventario

@app.patch("/inventario/{producto_id}")
async def actualizar_stock(producto_id: int, update_data: InventarioUpdate, session: AsyncSession = Depends(get_session)):
    # 1. Buscar el inventario de ese producto
    # Nota: Asumo que producto_id es único en la tabla de inventario
    statement = select(Inventario).where(Inventario.producto_id == producto_id)
    result = await session.execute(statement)
    inventario = result.scalars().first()

    if not inventario:
        raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
    
    # 2. Validar si hay suficiente stock
    if inventario.cantidad < update_data.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")
    
    # 3. Restar y guardar
    inventario.cantidad -= update_data.cantidad
    session.add(inventario)
    await session.commit()
    await session.refresh(inventario)

    return inventario

