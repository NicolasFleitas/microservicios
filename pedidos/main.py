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
        # 1.1 Validación: Ver que respondió el otro servicio (Productos)
        try: 
            resp_pedido = await client.get(f"http://localhost:8001/productos/{pedido_data.producto_id}")            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="El servicio de Productos no responde")

        # 1.2 VALIDACIÓN: Ver que respondió el otro servicio (Productos)  
        if resp_pedido.status_code == 404:
            raise HTTPException(status_code=404, detail="El producto no existe, no se puede crear el pedido")

        if resp_pedido.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al verificar el producto")
        
        # 2. Restar stock en Inventario
        # Enviamos un PATCH con la cantidad que pide el usuario
        payload = {"cantidad": pedido_data.cantidad}
        
        # 2.1 Validación: Ver que respondió el otro servicio (Inventario)
        try:
            resp_inventario = await client.patch(f"http://localhost:8002/inventario/{pedido_data.producto_id}", json=payload)
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="El servicio de Inventario no responde")
    
        # 2.2 Validación: Ver que respondió el otro servicio (Inventario)
        if resp_inventario.status_code == 404:
            raise HTTPException(status_code=404, detail="No se encontro el inventario para este producto")
        
        if resp_inventario.status_code == 400:
            # Si responde 400 es porque no hay stock suficiente segun logica del codigo.
            raise HTTPException(status_code=400, detail="No hay stock suficiente")
        
        if resp_inventario.status_code != 200:
            raise HTTPException(status_code=resp_inventario.status_code, detail="Error en el servicio de inventario")
    
    # 3. Guardar el Pedido si todo lo anterior paso.
    nuevo_pedido = Pedido.model_validate(pedido_data)
    nuevo_pedido.estado = "PENDIENTE"
    
    session.add(nuevo_pedido)
    await session.commit()
    await session.refresh(nuevo_pedido)

    return nuevo_pedido
    

