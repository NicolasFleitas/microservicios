from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL de conexión para la base de datos de autenticación
DATABASE_URL = os.getenv("AUTH_DB_URL", "sqlite+aiosqlite:///auth.db")

# El Motor
engine = create_async_engine(DATABASE_URL, future=True)

# Función para inicializar la DB (Crear tablas)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependencia para obtener la sesión
async def get_session():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
