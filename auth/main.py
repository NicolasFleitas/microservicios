from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from auth.database import init_db, get_session
from auth.models import Usuario
from auth.schemas import UsuarioCreate, UsuarioLogin, Token
from auth.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando base de datos de autenticacion")
    await init_db()
    yield
    print("Cerrando base de datos de autenticacion")

app = FastAPI(lifespan=lifespan)

@app.post("/register", response_model=Usuario)
async def register(usuario: UsuarioCreate, session: AsyncSession = Depends(get_session)):
    # Validar si existe
    statement = select(Usuario).where(Usuario.username == usuario.username)
    resultado = await session.execute(statement)
    if resultado.scalar_one_or_none(): # Devuelve el primer resultado o None si no hay ninguno
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    # Crear usuario
    hashed_pwd = get_password_hash(usuario.password)
    nuevo_usuario = Usuario(username=usuario.username, email=usuario.email, hashed_password=hashed_pwd)
    session.add(nuevo_usuario)
    await session.commit()
    await session.refresh(nuevo_usuario)
    return nuevo_usuario

@app.post("/login", response_model=Token)
async def login(form_data: UsuarioLogin, session: AsyncSession = Depends(get_session)):
    # Buscar usuario
    statement = select(Usuario).where(Usuario.username == form_data.username)
    resultado = await session.execute(statement)
    usuario_db = resultado.scalar_one_or_none()
    
    if not usuario_db or not verify_password(form_data.password, usuario_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario_db.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
