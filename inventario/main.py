import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

# Importación de modelos y la conexio
from inventario.database import init_db, get_session
from inventario.models import Inventario, InventarioCreate, InventarioUpdate
from inventario.dependencies import validar_token

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos Inventario")
    await init_db()
    yield
    print("Cerrando la base de datos Inventario")

app = FastAPI(dependencies=[Depends(validar_token)], lifespan=lifespan)

@app.get("/inventario", response_model=list[Inventario])
async def listar_inventario(session: AsyncSession = Depends(get_session)):
    statement = select(Inventario)
    resultado = await session.execute(statement)

    return resultado.scalars().all()

@app.post("/inventario", response_model=Inventario)
async def crear_inventario(
    inventario_data: InventarioCreate,
    session: AsyncSession = Depends(get_session)
):
    # 1. VALIDACIÓN EXTERNA: Ver si existe el producto
    headers_seguridad = {"Authorization": "Bearer " + os.getenv("SECRET_KEY")}
    
    async with httpx.AsyncClient() as client:
        try:
            # Llamamos al servicio de Productos
            resp = await client.get(
                f"http://127.0.0.1:8001/productos/{inventario_data.producto_id}",
                headers=headers_seguridad
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="No se pudo verificar el producto. Servicio productos caído.")
        
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"El producto ID {inventario_data.producto_id} no existe. No se puede crear inventario.")

    # VALIDACIÓN DE DUPLICADOS (Manejo de error de BD)
    try:
        nuevo_inventario = Inventario.model_validate(inventario_data)
        session.add(nuevo_inventario)
        await session.commit()
        await session.refresh(nuevo_inventario)
        return nuevo_inventario
    except Exception as e:
        await session.rollback() # IMPORTANNTE: Limpiar la sesión si falla
        raise HTTPException(status_code=400, detail="Ya existe un inventario para este producto ID")  

@app.patch("/inventario/{producto_id}")
async def actualizar_stock(producto_id: int, 
    update_data: InventarioUpdate,
    session: AsyncSession = Depends(get_session)
):
    # 1. Buscar el inventario de ese producto
    # Nota: Asumo que producto_id es único en la tabla de inventario
    statement = select(Inventario).where(Inventario.producto_id == producto_id)
    result = await session.execute(statement)
    inventario = result.scalars().first()

    if not inventario:
        raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
    
    # 2. Validar si hay suficiente stock
    
    # 3. Cambiar cantidad depende del tipo movimiento
    if update_data.tipo_movimiento == "SALIDA":
        if inventario.cantidad < update_data.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
        inventario.cantidad -= update_data.cantidad

    elif update_data.tipo_movimiento == "ENTRADA":
        inventario.cantidad += update_data.cantidad
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimiento no válido")

    session.add(inventario)
    await session.commit()
    await session.refresh(inventario)

    return inventario

@app.get("/inventario/{producto_id}", response_model=Inventario)
async def verificar_stock(producto_id: int, session: AsyncSession = Depends(get_session)):
    # Busca por la columna producto_id, NO por la primary key de la tabla Inventario
    statement = select(Inventario).where(Inventario.producto_id == producto_id)
    resultado = await session.execute(statement)
    inventario = resultado.scalars().first()

    if not inventario:
        raise HTTPException(status_code=404, detail="No existe inventario para este producto")
    
    return inventario


