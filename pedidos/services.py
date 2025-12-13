import os 
import httpx
import aiobreaker
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pedidos.models import Pedido, PedidoCreate, PedidoUpdate
from pedidos.logger_config import configurar_logger

SECRET_KEY = os.getenv("SECRET_KEY")

# Configuración de Circuit Breaker
breaker_inventario = aiobreaker.CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=60))
breaker_productos = aiobreaker.CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=60))

# Configuración del logger
logger = configurar_logger("PEDIDOS-SERVICE")

class PedidoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.headers = {"Authorization": f"Bearer {SECRET_KEY}"}
    
    # ZONA DE RESILIENCIA
    # CASO 1: Llamada a PRODUCTOS
    @breaker_productos
    @retry(
            stop=stop_after_attempt(3), # Intenta 3 veces
            wait=wait_fixed(2), # Espera 2 segundos entre intentos
            retry=retry_if_exception_type(httpx.RequestError),
            reraise=True # Si falla 3 veces, lanza el error original
        )
    async def _llamada_productos(self, method: str, url: str):
        logger.info(f"Conectando con Productos -> {method} {url}")
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, headers=self.headers)
    
    # CASO 2: Llamada a INVENTARIO
    @breaker_inventario
    @retry (
            stop=stop_after_attempt(3),
            wait=wait_fixed(2),
            retry=retry_if_exception_type(httpx.RequestError),
            reraise=True
    )
    async def _llamada_inventario(self, method: str, url: str, json: dict = None):
        logger.info(f"Conectando con Inventario -> {method} {url}")
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, json=json, headers=self.headers)

    # LOGICA DE NEGOCIO - CREAR PEDIDO
    async def crear_pedido(self, pedido_data: PedidoCreate):
        """ Crea un pedido orquestando validaciones, inventario y persistencia """

        logger.info(f"Inicio de proceso de pedido. ProductoID: {pedido_data.producto_id}")
        try:
            # 1. Validar que el producto exista en el catálogo
            await self._validar_producto(pedido_data.producto_id)
            
            # 2. Restar Stock en Inventario
            await self._actualizar_stock(pedido_data.producto_id, pedido_data.cantidad, "SALIDA")
            
            # 3. Guardar pedido en DB local con manejo de errores (Compensación)
            resultado = await self._guardar_pedido_con_compensacion(pedido_data)
            logger.info(f"Pedido {resultado.id} creado exitosamente.")
            return resultado
        except Exception as e:
            # LOG DE ERROR CRITICO
            logger.error(f"Error al crear pedido: {str(e)}")
            raise e
    
    async def _validar_producto(self, producto_id: int):
        try:
            resp = await self._llamada_productos(
                "GET", 
                f"http://127.0.0.1:8001/productos/{producto_id}"
            )
        except aiobreaker.CircuitBreakerError:
            # Capturamos si el circuito esta abierto
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El catálogo de productos no responde temporalmente (Circuit open)"
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Error de conexión con Productos")

        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

    async def _actualizar_stock(self, producto_id: int, cantidad: int, tipo_movimiento: str):
        payload = {"cantidad": cantidad, "tipo_movimiento": tipo_movimiento}
        try:
            resp = await self._llamada_inventario(
                "PATCH",
                f"http://127.0.0.1:8002/inventario/{producto_id}",
                json=payload
            )
        except aiobreaker.CircuitBreakerError:
            raise HTTPException(
                # Capturamos si el circuito esta abierto
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail= "El sistema de inventario no responde temporalmente (Circuit Open)."
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503,
            detail="Servicio de Inventario no disponible")

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail"))

    async def _guardar_pedido_con_compensacion(self, pedido_data: PedidoCreate):
        nuevo_pedido = Pedido.model_validate(pedido_data)
        nuevo_pedido.estado = "PENDIENTE"
        self.db.add(nuevo_pedido)

        try:
            await self.db.commit()
            await self.db.refresh(nuevo_pedido)
            return nuevo_pedido
        except Exception:
            await self.db.rollback()
            # Si falla la BD, debemos devolver el stock que ya restamos
            await self._compensar_stock(pedido_data.producto_id, pedido_data.cantidad)
            raise HTTPException(status_code=500, detail="Error interno. Pedido revertido.")

    async def _compensar_stock(self, producto_id: int, cantidad: int):
        try:
            # Reutilizamos la lógica de actualizar stock pero ignoramos errores HTTP
            await self._actualizar_stock(producto_id, cantidad, "ENTRADA")
        except HTTPException:            
            logger.critical(f"CRITICO: Falló compensación de stock para producto {producto_id} con cantidad: {cantidad}")

    # LOGICA DE NEGOCIO - MODIFICAR PEDIDO
    async def modificar_pedido(self, pedido_id: int, pedido_data: PedidoUpdate):
        """ Modifica un pedido existente gestionando validaciones y stock """
        
        # 1. Obtener pedido
        logger.info(f"Modificando pedido {pedido_id} -> Nuevo Estado: {pedido_data.estado}")
        pedido_db = await self._obtener_pedido(pedido_id)
        
        # 2. Validar transición
        self._validar_transicion_estado(pedido_db, pedido_data.estado)

        # 3. Gestionar SAGA (Devolución de stock si se cancela)
        if self._es_cancelacion(pedido_db, pedido_data.estado):
            # Reutilizamos _actualizar_stock para devolver ("ENTRADA")
            await self._actualizar_stock(pedido_db.producto_id, pedido_db.cantidad, "ENTRADA")

        # 4. Actualizar estado
        pedido_actualizado = await self._actualizar_estado_pedido(pedido_db, pedido_data.estado)
        logger.info(f"Pedido {pedido_id} actualizado correctamente a {pedido_data.estado}")
        return pedido_actualizado

    async def _obtener_pedido(self, pedido_id: int) -> Pedido:
        pedido = await self.db.get(Pedido, pedido_id)
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return pedido

    def _validar_transicion_estado(self, pedido: Pedido, nuevo_estado: str):
        if nuevo_estado not in ["PENDIENTE", "COMPLETADO", "CANCELADO"]:
            raise HTTPException(status_code=400, detail="Estado inválido. Estados permitidos: PENDIENTE, COMPLETADO, CANCELADO")

        if nuevo_estado == "COMPLETADO" and pedido.estado == "CANCELADO":
            raise HTTPException(status_code=400, detail="No se puede completar un pedido que ya está cancelado")

        if nuevo_estado == "CANCELADO" and pedido.estado == "COMPLETADO":
            raise HTTPException(status_code=400, detail="No se puede cancelar un pedido que ya está completado")

    def _es_cancelacion(self, pedido: Pedido, nuevo_estado: str) -> bool:
        return nuevo_estado == "CANCELADO" and pedido.estado != "CANCELADO"

    async def _actualizar_estado_pedido(self, pedido: Pedido, nuevo_estado: str):
        pedido.estado = nuevo_estado
        self.db.add(pedido)
        try:
            await self.db.commit()
            await self.db.refresh(pedido)
            return pedido
        except Exception as e:
            logger.error(f"Error crítico DB al actualizar estado del pedido {pedido.id} a '{nuevo_estado}': {str(e)}")
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Error interno al actualizar estado del pedido")

    