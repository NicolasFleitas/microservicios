from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select


from productos.models import Producto, ProductoCreate, ProductoUpdate
from productos.logger_config import configurar_logger

logger = configurar_logger("PRODUCTOS-SERVICE")

class ProductoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_producto(self, producto_data: ProductoCreate) -> Producto:
        logger.info(f"Intentando crear producto: {producto_data.nombre}")
        nuevo_producto = Producto.model_validate(producto_data)
        self.db.add(nuevo_producto)
        try:
            await self.db.commit()
            await self.db.refresh(nuevo_producto)
            logger.info(f"Producto creado exitosamente con ID: {nuevo_producto.id}")
            return nuevo_producto
        except IntegrityError:
            await self.db.rollback()
            logger.warning(f"Intento de duplicado: {producto_data.nombre}")
            raise HTTPException(status_code=400, detail="El producto ya existe")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error al crear producto: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al crear producto: {str(e)}")

    async def listar_productos(self) -> list[Producto]:
        """ Devuelve todos los productos ordenados por ID """
        statement = select(Producto).order_by(Producto.id).limit(100)
        resultado = await self.db.execute(statement)
        return resultado.scalars().all()

    async def leer_producto(self, producto_id: int) -> Producto:
        """ Devuelve un producto por su ID """
        producto = await self.db.get(Producto, producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return producto

    async def actualizar_producto(self, producto_id: int, producto_data: ProductoUpdate) -> Producto:
        logger.info(f"Actualizando producto {producto_id}")
        producto_db = await self.leer_producto(producto_id)
        
        producto_data_dict = producto_data.model_dump(exclude_unset=True)
        for key, value in producto_data_dict.items():
            setattr(producto_db, key, value)
            
        self.db.add(producto_db)
        try:
            await self.db.commit()
            await self.db.refresh(producto_db)
            logger.info(f"Producto {producto_id} actualizado exitosamente")
            return producto_db
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error al actualizar producto {producto_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al actualizar producto: {str(e)}")
