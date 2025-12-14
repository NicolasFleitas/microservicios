import os
import httpx
import jwt
import aiobreaker
import contextlib
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("SECRET_KEY")

# --- CONFIGURACIÓN DE RESILIENCIA ---
breaker_productos = aiobreaker.CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=60))

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

    @contextlib.asynccontextmanager
    async def _control_errores(self, nombre_servicio: str):
        try:
            yield
        except aiobreaker.CircuitBreakerError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"El sistema de {nombre_servicio} no responde temporalmente (Circuit Open)."
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error de conexión con {nombre_servicio}"
            )

class ProductoClient(BaseClient):
    BASE_URL = "http://127.0.0.1:8001/productos"

    @breaker_productos
    @RETRY_POLICY
    async def check_producto_exists(self, producto_id: int):
        async with self._control_errores("Productos"):
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
