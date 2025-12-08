import os 
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pedidos.models import Pedido, PedidoCreate, PedidoUpdate

SECRET_KEY = os.getenv("SECRET_KEY")

class PedidoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.headers = {"Authorization": f"Bearer {SECRET_KEY}"}
    
    # ZONA DE RESILIENCIA
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True # Si falla 3 veces, lanza el error original
    )
    async def _llamada_resiliente(self, method: str, url: str, json: dict = None):
        async with httpx.AsyncClient() as client:
            if method == "GET":
                return await client.get(url, headers=self.headers)
            elif method == "PATCH":
                return await client.patch(url, json=json, headers=self.headers)
    
    # LOGICA DE NEGOCIO
    async def crear_pedido(self, pedido_data: PedidoCreate):
        # 1. Validar Producto
        try:
            resp_prod = await self._llamada_resiliente(
                "GET",
                f"http://127.0.0.1:8001/productos/{pedido_data.producto_id}"
            )
        except httpx.RequestError:
            # Si tenacity se rinde después de 3 intentos, entra acá.
            raise HTTPException(status_code=503, detail="Servicio de Productos no disponible (TimeOut)")
        
        if resp_prod.status_code == 404:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # 2. Restar Stock (Servicio inventario)
        payload = {"cantidad": pedido_data.cantidad, "tipo_movimiento": "SALIDA"}
        try: 
            resp_inv = await self._llamada_resiliente(
                "PATCH",
                f"http://127.0.0.1:8002/inventario/{pedido_data.producto_id}",
                json=payload
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de inventario no disponible")
        
        if resp_inv.status_code != 200:
            # Pasamos el error que nos dio el inventario (ej: Stock insuficiente)
            raise HTTPException(status_code=resp_inv.status_code, detail=resp_inv.json().get("detail"))
        
        # 3. Guardar pedido
        nuevo_pedido = Pedido.model_validate(pedido_data)
        nuevo_pedido.estado = "PENDIENTE"

        self.db.add(nuevo_pedido)
        await self.db.commit()
        await self.db.refresh(nuevo_pedido)

        return nuevo_pedido

    async def modificar_pedido(self, pedido_id: int, pedido_data: PedidoUpdate):
        # 1. Buscar el pedido
        pedido_db = await self.db.get(Pedido, pedido_id)

        if not pedido_db:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # 2. LOGICA DE COMPENSACIÓN
        # Si el estado nuevo es CANCELADO y el estado anterior NO ERA Cancelado
        if pedido_data.estado == "CANCELADO" and pedido_db.estado != "CANCELADO":
            payload = {
                "cantidad": pedido_db.cantidad, 
                "tipo_movimiento": "ENTRADA"
            }
            try:
                # Usamos la llamada resiliente existente
                resp_inventario = await self._llamada_resiliente(
                    "PATCH",
                    f"http://127.0.0.1:8002/inventario/{pedido_db.producto_id}",
                    json=payload
                )
            except httpx.RequestError:
                raise HTTPException(status_code=503, detail="Error de conexión con Inventario (Compensación fallida)")
            
            if resp_inventario.status_code != 200:
                raise HTTPException(status_code=resp_inventario.status_code, detail=f"Error en inventario: {resp_inventario.text}")

        # 3. Actualizar estado
        pedido_db.estado = pedido_data.estado
        self.db.add(pedido_db)
        await self.db.commit()
        await self.db.refresh(pedido_db)
        return pedido_db

    