import os
import httpx
import jwt
import aiobreaker
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from fastapi import HTTPException
from pedidos.logger_config import configurar_logger

SECRET_KEY = os.getenv("SECRET_KEY")
logger = configurar_logger("PEDIDOS-CLIENTS")

# --- CONFIGURACIÓN DE RESILIENCIA ---
# Los breakers excluyen HTTPException porque son errores de negocio (404, 400, etc.)
# Solo los errores de conexión (httpx.RequestError) deberían abrir el circuito
breaker_inventario = aiobreaker.CircuitBreaker(
    fail_max=5, 
    timeout_duration=timedelta(seconds=60),
    exclude=[HTTPException]
)
breaker_productos = aiobreaker.CircuitBreaker(
    fail_max=5, 
    timeout_duration=timedelta(seconds=60),
    exclude=[HTTPException]
)

RETRY_POLICY = retry(
    stop=stop_after_attempt(3), 
    wait=wait_fixed(2), 
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True
)

class BaseClient:
    def __init__(self):
        # Generar token de sistema para llamadas internas
        token = jwt.encode({"sub": "sistema-pedidos"}, SECRET_KEY, algorithm="HS256")
        self.headers = {"Authorization": f"Bearer {token}"}


class ProductoClient(BaseClient):
    BASE_URL = "http://127.0.0.1:8001/productos"

    @breaker_productos
    @RETRY_POLICY
    async def get_producto(self, producto_id: int):
        """
        Obtiene un producto del servicio de Productos.
        Los errores se propagan al servicio para manejo centralizado.
        """
        logger.info(f"Conectando con Productos -> GET {self.BASE_URL}/{producto_id}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/{producto_id}", headers=self.headers)
        
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return resp


class InventarioClient(BaseClient):
    BASE_URL = "http://127.0.0.1:8002/inventario"

    @breaker_inventario
    @RETRY_POLICY
    async def actualizar_stock(self, producto_id: int, cantidad: int, tipo_movimiento: str):
        """
        Actualiza el stock en el servicio de Inventario.
        Los errores se propagan al servicio para manejo centralizado.
        """
        payload = {"cantidad": cantidad, "tipo_movimiento": tipo_movimiento}
        logger.info(f"Conectando con Inventario -> PATCH {self.BASE_URL}/{producto_id}")
        
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.BASE_URL}/{producto_id}", 
                json=payload, 
                headers=self.headers
            )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail"))
        return resp

