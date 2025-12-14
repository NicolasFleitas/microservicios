import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importación de modelos y la conexion
from inventario.database import init_db, get_session
from inventario.models import Inventario, InventarioCreate, InventarioUpdate
from inventario.dependencies import validar_token
from inventario.services import InventarioService

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos Inventario")
    await init_db()
    yield
    print("Cerrando la base de datos Inventario")

app = FastAPI(
    dependencies=[Depends(validar_token)], 
    lifespan=lifespan
)

# --- ENDPOINTS ---

# 1. Crear (POST /inventario)
@app.post("/inventario", response_model=Inventario)
async def crear_inventario(
    inventario_data: InventarioCreate,
    session: AsyncSession = Depends(get_session)
):
    servicio = InventarioService(session)
    return await servicio.crear_inventario(inventario_data)

# 2. Listar (GET /inventario)
@app.get("/inventario", response_model=list[Inventario])
async def listar_inventario(session: AsyncSession = Depends(get_session)):
    statement = select(Inventario)
    resultado = await session.execute(statement)

    return resultado.scalars().all()

# 3. Leer Uno (GET /inventario/{id})
@app.get("/inventario/{producto_id}", response_model=Inventario)
async def verificar_stock(producto_id: int, session: AsyncSession = Depends(get_session)):
    servicio = InventarioService(session)
    return await servicio.verificar_stock(producto_id)

# 4. Actualizar (PATCH /inventario/{id})
@app.patch("/inventario/{producto_id}")
async def actualizar_stock(producto_id: int, 
    update_data: InventarioUpdate,
    session: AsyncSession = Depends(get_session)
):
    servicio = InventarioService(session)
    return await servicio.actualizar_stock(producto_id, update_data)
