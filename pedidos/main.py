from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from pedidos.database import init_db, get_session
from pedidos.models import Pedido, PedidoCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando base de datos de pedidos")
    await init_db()
    yield
    print("Cerrando base de datos de pedidos")

app = FastAPI(lifespan=lifespan)

@app.post("/pedidos", response_model=Pedido)
async def crear_pedido(pedido_data: PedidoCreate, session: AsyncSession = Depends(get_session)):

    # 1. COMUNICACIÓN: Validar si el producto existe
    # Usamos un bloque 'async with' para abrir y cerrar la conexión eficientemente
    async with httpx.AsyncClient() as client:

        try: 
            response = await client.get(f"http://localhost:8001/productos/{pedido_data.producto_id}") 
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="El servicio de Productos no responde")

    # 2. VALIDACIÓN: Ver que respondió el otro servicio
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="El producto no existe, no se puede crear el pedido")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error al verificar el producto")
    
    # 3. ÉXITO: Si llega acá, el producto existe. Guardamos el pedido.
    nuevo_pedido = Pedido.model_validate(pedido_data)
    session.add(nuevo_pedido)
    await session.commit()
    await session.refresh(nuevo_pedido)

    return nuevo_pedido
    

