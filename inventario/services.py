from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from inventario.models import Inventario, InventarioCreate, InventarioUpdate
from inventario.clients import ProductoClient

class InventarioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.producto_client = ProductoClient()

    async def crear_inventario(self, inventario_data: InventarioCreate) -> Inventario:
        # 1. Validar que el producto existe en el otro servicio
        await self.producto_client.check_producto_exists(inventario_data.producto_id)

        # 2. Guardar en DB
        try:
            nuevo_inventario = Inventario.model_validate(inventario_data)
            self.db.add(nuevo_inventario)
            await self.db.commit()
            await self.db.refresh(nuevo_inventario)
            return nuevo_inventario
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Ya existe un inventario para este producto ID")

    async def actualizar_stock(self, producto_id: int, update_data: InventarioUpdate) -> Inventario:
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
        self.db.add(inventario)
        await self.db.commit()
        await self.db.refresh(inventario)
        return inventario

    async def verificar_stock(self, producto_id: int) -> Inventario:
        return await self._obtener_inventario(producto_id)

    async def _obtener_inventario(self, producto_id: int) -> Inventario:
        statement = select(Inventario).where(Inventario.producto_id == producto_id)
        resultado = await self.db.execute(statement)
        inventario = resultado.scalars().first()

        if not inventario:
            raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
        return inventario
