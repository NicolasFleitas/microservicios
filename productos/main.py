from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importación de modelos y la conexión
from productos.database import init_db, get_session
from productos.models import Producto, ProductoCreate

#Lifespan (Ciclo de vida): Código que corre antes de que la app empiece a recibir peticiones
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos")
    await init_db() # Se crean las tablas
    yield
    print("Cerrando la base de datos")
    
# Instanciamos la app
app = FastAPI(lifespan=lifespan)

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

# 4. Leer raíz
@app.get("/")
def leer_raiz():
    return {"mensaje" : "Hola, bienvenido al microservicio de productos" }

