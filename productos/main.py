from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

# Importaciones de dependencias y modelos 
from productos.database import init_db, get_session, engine
from productos.models import Producto, ProductoCreate, ProductoUpdate
from productos.dependencies import validar_token
from productos.services import ProductoService

#Lifespan (Ciclo de vida): Código que corre antes de que la app empiece a recibir peticiones
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos")
    await init_db() # Se crean las tablas
    yield
    print("Cerrando la base de datos")
    await engine.dispose()
    
# Instanciamos la app
app = FastAPI(
    title="Productos Service",
    dependencies=[Depends(validar_token)],
    lifespan=lifespan
)

# --- ENDPOINTS ---

# 1. Crear Producto
@app.post("/productos", response_model=Producto)
async def crear_producto(producto_data: ProductoCreate, session: AsyncSession = Depends(get_session)):
    service = ProductoService(session)
    return await service.crear_producto(producto_data)

# 2. Listar productos
@app.get("/productos", response_model=list[Producto])
async def listar_productos(session: AsyncSession = Depends(get_session)):
    service = ProductoService(session)
    return await service.listar_productos()

@app.get("/productos/{producto_id}", response_model=Producto)
async def leer_producto(producto_id: int, session: AsyncSession = Depends(get_session)):
    service = ProductoService(session)
    return await service.leer_producto(producto_id)

@app.patch("/productos/{producto_id}", response_model=Producto)
async def actualizar_producto(producto_id: int, producto_data: ProductoUpdate, session: AsyncSession = Depends(get_session)):
    service = ProductoService(session)
    return await service.actualizar_producto(producto_id, producto_data)
