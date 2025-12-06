from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importación de modelos y la conexio
from inventario.database import init_db, get_session
from inventario.models import Inventario, InventarioCreate, InventarioUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos Inventario")
    await init_db()
    yield
    print("Cerrando la base de datos Inventario")

app = FastAPI(lifespan=lifespan)

security = HTTPBearer()

TOKEN_SECRETO = "clavesecreta123!"

def validar_token(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token_recibido = credenciales.credentials
    if token_recibido != TOKEN_SECRETO:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas. Acceso denegado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_recibido

@app.post("/inventario", response_model=Inventario)
async def crear_inventario(inventario_data: InventarioCreate, session: AsyncSession = Depends(get_session)):
   
    nuevo_inventario = Inventario.model_validate(inventario_data)

    session.add(nuevo_inventario)
    await session.commit()
    await session.refresh(nuevo_inventario)

    return nuevo_inventario

@app.patch("/inventario/{producto_id}")
async def actualizar_stock(producto_id: int, 
    update_data: InventarioUpdate,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(validar_token)
):
    # 1. Buscar el inventario de ese producto
    # Nota: Asumo que producto_id es único en la tabla de inventario
    statement = select(Inventario).where(Inventario.producto_id == producto_id)
    result = await session.execute(statement)
    inventario = result.scalars().first()

    if not inventario:
        raise HTTPException(status_code=404, detail="Inventario no encontrado para este producto")
    
    # 2. Validar si hay suficiente stock
    if inventario.cantidad < update_data.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")
    
    # 3. Restar y guardar
    inventario.cantidad -= update_data.cantidad
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


