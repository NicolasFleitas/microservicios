from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importaciones de dependencias y modelos 
from productos.database import init_db, get_session
from productos.models import Producto, ProductoCreate, ProductoUpdate
from productos.dependencies import validar_token

#Lifespan (Ciclo de vida): Código que corre antes de que la app empiece a recibir peticiones
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos")
    await init_db() # Se crean las tablas
    yield
    print("Cerrando la base de datos")
    
# Instanciamos la app
app = FastAPI(dependencies=[Depends(validar_token)], lifespan=lifespan)

# --- ENDPOINTS ---

# 1. Crear Producto
# Usamos response_model=Producto para devolver el objeto COMPLETO (con ID) al usuario.
@app.post("/productos", response_model=Producto)
async def crear_producto(producto_data: ProductoCreate, session: AsyncSession = Depends(get_session)):
    # Convertimos el modelo de entrada (ProductoCreate) al modelo de tabla (Producto)
    nuevo_producto = Producto.model_validate(producto_data)

    session.add(nuevo_producto)   # Agregamos a la sesión (memoria)
    await session.commit()        # Guardamos en DBB (Confirmar cambios)
    await session.refresh(nuevo_producto) # Recargamos el objeto para obtener el ID

    return nuevo_producto

# 2. Listar productos
@app.get("/productos", response_model=list[Producto])
async def listar_productos(session: AsyncSession = Depends(get_session)):
    # Creamos la sentencia SQL: SELECT * FROM producto
    statement = select(Producto)

    # Ejecutamos la consulta de forma asíncrona
    resultado = await session.execute(statement)

    # .scalars() extrae el objeto de la tupla y .all() lo convierte en lista
    return resultado.scalars().all()

@app.get("/productos/{producto_id}", response_model=Producto)
async def leer_producto(producto_id: int, session: AsyncSession = Depends(get_session)):
    # session.get es un atajo muy útil para buscar por primary Key
    producto = await session.get(Producto, producto_id)

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto

@app.patch("/productos/{producto_id}", response_model=Producto)
async def actualizar_producto(producto_id: int, producto_data: ProductoUpdate, session: AsyncSession = Depends(get_session)):
    # 1. Buscar el producto
    producto_db = await session.get(Producto, producto_id)

    if not producto_db:
        HTTPException(status_code=404, detail="Producto no encontrado")
    
    # 2. Actualizar los campos
    # Esto copia los datos de 'producto_data' dentro de 'producto_db'
    producto_data_dict = producto_data.model_dump(exclude_unset=True) # exclude_unset=True excluye los campos que no se envían

    for key, value in producto_data_dict.items():
        setattr(producto_db, key, value)
    
    # 3. Guardar cambios
    session.add(producto_db)
    await session.commit()
    await session.refresh(producto_db)

    return producto_db


# 4. Leer raíz
@app.get("/")
def leer_raiz():
    return {"mensaje" : "Hola, bienvenido al microservicio de productos" }

