from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 1. La URL de conexión.
# OJO: Nota el "postgresql+asyncpg". Le decimos que use el driver asíncrono.
DATABASE_URL = "postgresql+asyncpg://postgres:penguin@localhost/tienda_inventario"

# 2. El Motor. Es el coordinador de la conexión
# echo=True sirve para mostrar los SQLs en la consola (para debug
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 3. Función para inicializar la DB (Crear tablas)
async def init_db():
    async with engine.begin() as conn:
    # Esto busca todos los modelos que hereden de SQLModel y crea las tablas
        await conn.run_sync(SQLModel.metadata.create_all)

# 4. Dependencia para obtener la sesión
# Esto se usara en cada endpoint para interactuar con la DB
async def get_session():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session