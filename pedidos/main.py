
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from pedidos.database import init_db, get_session
from pedidos.models import Pedido, PedidoCreate, PedidoUpdate
from pedidos.dependencies import validar_token
from pedidos.services import PedidoService

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando base de datos de pedidos")
    await init_db()
    yield
    print("Cerrando base de datos de pedidos")

app = FastAPI(dependencies=[Depends(validar_token)], lifespan=lifespan)

@app.post("/pedidos", response_model=Pedido)
async def crear_pedido(
        pedido_data: PedidoCreate,
        session: AsyncSession = Depends(get_session)
):
    """ Crea un nuevo pedido """
    # 1. Instanciamos el servicio pasándole la sesión de la DB
    servicio = PedidoService(session) 
    return await servicio.crear_pedido(pedido_data)

@app.patch("/pedidos/{pedido_id}", response_model=Pedido)
async def modificar_pedido(pedido_id: int, pedido_data: PedidoUpdate, session: AsyncSession = Depends(get_session)):
    """ Actualiza solamente el estado del pedido """
    servicio = PedidoService(session)
    return await servicio.modificar_pedido(pedido_id, pedido_data)

    

