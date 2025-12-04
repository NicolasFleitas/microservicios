from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importación de modelos y la conexio
from inventario.database import init_db, get_session
from inventario.models import Inventario, InventarioCreate

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

