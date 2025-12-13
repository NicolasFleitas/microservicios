from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pedidos.models import Pedido, PedidoCreate, PedidoUpdate
from pedidos.logger_config import configurar_logger
from pedidos.clients import ProductoClient, InventarioClient

# Configuración del logger
logger = configurar_logger("PEDIDOS-SERVICE")

class PedidoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.producto_client = ProductoClient()
        self.inventario_client = InventarioClient()
    
    # LOGICA DE NEGOCIO - CREAR PEDIDO
    async def crear_pedido(self, pedido_data: PedidoCreate):
        """ Crea un pedido orquestando validaciones, inventario y persistencia """

        logger.info(f"Inicio de proceso de pedido. ProductoID: {pedido_data.producto_id}")
        try:
            # 1. Validar que el producto exista en el catálogo
            await self.producto_client.get_producto(pedido_data.producto_id)
            
            # 2. Restar Stock en Inventario
            await self.inventario_client.actualizar_stock(pedido_data.producto_id, pedido_data.cantidad, "SALIDA")
            
            # 3. Guardar pedido en DB local con manejo de errores (Compensación)
            resultado = await self._guardar_pedido_con_compensacion(pedido_data)
            logger.info(f"Pedido {resultado.id} creado exitosamente.")
            return resultado
        except Exception as e:
            # LOG DE ERROR CRITICO
            logger.error(f"Error al crear pedido: {str(e)}")
            raise e
    
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
            await self.inventario_client.actualizar_stock(producto_id, cantidad, "ENTRADA")
        except HTTPException:            
            logger.critical(f"CRITICO: Falló compensación de stock para producto {producto_id} con cantidad: {cantidad}")

    # LOGICA DE NEGOCIO - MODIFICAR PEDIDO
    async def modificar_pedido(self, pedido_id: int, pedido_data: PedidoUpdate):
        """ Modifica un pedido existente gestionando validaciones y stock """
        
        logger.info(f"Modificando pedido {pedido_id} -> Nuevo Estado: {pedido_data.estado}")
        try:
            # 1. Obtener pedido
            pedido_db = await self._obtener_pedido(pedido_id)
            
            # 2. Validar transición
            self._validar_transicion_estado(pedido_db, pedido_data.estado)

            # 3. Gestionar SAGA (Devolución de stock si se cancela)
            if self._es_cancelacion(pedido_db, pedido_data.estado):
                # Reutilizamos _actualizar_stock para devolver ("ENTRADA")
                await self.inventario_client.actualizar_stock(pedido_db.producto_id, pedido_db.cantidad, "ENTRADA")

            # 4. Actualizar estado
            pedido_actualizado = await self._actualizar_estado_pedido(pedido_db, pedido_data.estado)
            logger.info(f"Pedido {pedido_id} actualizado correctamente a {pedido_data.estado}")
            return pedido_actualizado

        except Exception as e:
            logger.error(f"Error al modificar pedido {pedido_id}: {str(e)}")
            raise e

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