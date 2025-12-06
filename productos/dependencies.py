import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

API_TOKEN_SECRETO = os.getenv("SECRET_KEY")

security = HTTPBearer()

async def validar_token(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependencia de seguridad.
    1. HTTPBearer se encarga de verificar que venga el header 'Authorization'.
    2. Se encarga de verificar que empiece con 'Bearer '.
    3. Nos entrega el token limpio en credenciales.credentials.
    """
    token_recibido = credenciales.credentials

    if token_recibido != API_TOKEN_SECRETO:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas. Acceso denegado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_recibido