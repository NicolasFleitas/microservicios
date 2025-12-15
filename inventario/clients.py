import os
import httpx
import jwt
import aiobreaker
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from fastapi import HTTPException
from inventario.logger_config import configurar_logger

SECRET_KEY = os.getenv("SECRET_KEY")
logger = configurar_logger("INVENTARIO-CLIENTS")

# --- CONFIGURACIÓN DE RESILIENCIA ---
# El breaker excluye HTTPException porque son errores de negocio (404, 400, etc.)
# Solo los errores de conexión (httpx.RequestError) deberían abrir el circuito
breaker_productos = aiobreaker.CircuitBreaker(
    fail_max=5, 
    timeout_duration=timedelta(seconds=60),
    exclude=[HTTPException]  # No contar errores de negocio como fallos
)

RETRY_POLICY = retry(
    stop=stop_after_attempt(3), 
    wait=wait_fixed(2), 
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True
)

class BaseClient:
    def __init__(self, service_name_sub="sistema-inventario"):
        # Generar token de sistema para llamadas internas
        token = jwt.encode({"sub": service_name_sub}, SECRET_KEY, algorithm="HS256")
        self.headers = {"Authorization": f"Bearer {token}"}


class ProductoClient(BaseClient):
    BASE_URL = "http://127.0.0.1:8001/productos"

    @breaker_productos
    @RETRY_POLICY
    async def check_producto_exists(self, producto_id: int):
        """
        Verifica si un producto existe en el servicio de Productos.
        Los errores se propagan al servicio para manejo centralizado.
        """
        logger.info(f"Verificando existencia en Productos -> GET {self.BASE_URL}/{producto_id}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/{producto_id}",
                headers=self.headers
            )
        
        if resp.status_code == 404:
            raise HTTPException(
                status_code=404, 
                detail=f"El producto ID {producto_id} no existe. No se puede crear inventario."
            )
        return True

