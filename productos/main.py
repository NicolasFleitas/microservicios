from fastapi import FastAPI
from contextlib import asynccontextmanager
from productos.database import init_db

#Lifespan (Ciclo de vida): Código que corre antes de que la app empiece a recibir peticiones
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando la base de datos")
    await init_db() # Se crean las tablas
    yield
    print("Cerrando la base de datos")
    
# Instanciamos la app
app = FastAPI(lifespan=lifespan)

@app.get("/")
def leer_raiz():
    return {"mensaje" : "El servicio de productos esta activado" }

