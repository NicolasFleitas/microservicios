from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from inventario.models import Inventario, InventarioCreate, InventarioUpdate
from inventario.clients import ProductoClient
from inventario.logger_config import configurar_logger

# Configuración del logger
logger = configurar_logger("INVENTARIO-SERVICE")

class InventarioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.producto_client = ProductoClient()

    async def crear_inventario(self, inventario_data: InventarioCreate) -> Inventario:
        logger.info(f"Inicio creación de inventario. ProductoID: {inventario_data.producto_id}")
        # 1. Validar que el producto existe en el otro servicio
        await self.producto_client.check_producto_exists(inventario_data.producto_id)

        # 2. Guardar en DB
        try:
            nuevo_inventario = Inventario.model_validate(inventario_data)
            self.db.add(nuevo_inventario)
            await self.db.commit()
            await self.db.refresh(nuevo_inventario)
            logger.info(f"Inventario creado exitosamente para producto {inventario_data.producto_id}")
            return nuevo_inventario
        except Exception as e:
            logger.error(f"Error al crear inventario: {str(e)}")
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Ya existe un inventario para este producto ID")

    async def actualizar_stock(self, producto_id: int, update_data: InventarioUpdate) -> Inventario:
        logger.info(f"Actualizando stock. Producto: {producto_id}, Tipo: {update_data.tipo_movimiento}, Cantidad: {update_data.cantidad}")
        # 1. Buscar inventario
        inventario = await self._obtener_inventario(producto_id)
        
        # 2. Lógica de negocio entradas/salidas
        if update_data.tipo_movimiento == "SALIDA":
            if inventario.cantidad < update_data.cantidad:
                raise HTTPException(status_code=400, detail="Stock insuficiente")
            inventario.cantidad -= update_data.cantidad

        elif update_data.tipo_movimiento == "ENTRADA":
            inventario.cantidad += update_data.cantidad
        else:
            raise HTTPException(status_code=400, detail="Tipo de movimiento no válido")

        # 3. Guardar
        try:
            self.db.add(inventario)
            await self.db.commit()
            await self.db.refresh(inventario)
            logger.info(f"Stock actualizado correctamente. Nuevo total: {inventario.cantidad}")
            return inventario
        except Exception as e:
            logger.error(f"Error crítico DB al actualizar stock del producto {producto_id}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Error interno al actualizar stock")

    async def verificar_stock(self, producto_id: int) -> Inventario:
        return await self._obtener_inventario(producto_id)

    async def _obtener_inventario(self, producto_id: int) -> Inventario:
        statement = select(Inventario).where(Inventario.producto_id == producto_id)
        resultado = await self.db.execute(statement)
        inventario = resultado.scalars().first()

        if not inventario:
            raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
        return inventario
