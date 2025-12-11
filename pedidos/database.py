from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# URL de conexión.
DATABASE_URL = "postgresql+asyncpg://postgres:penguin@localhost/tienda_pedidos"

# El Motor. Es el coordinador de la conexión
engine = create_async_engine(DATABASE_URL, future=True)

# Función para inicializar la DB (Crear tablas)
async def init_db():
    async with engine.begin() as conn:
    # Esto busca todos los modelos que hereden de SQLModel y crea las tablas
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependencia para obtener la sesión
# Esto se usara en cada endpoint para interactuar con la DB
async def get_session():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session