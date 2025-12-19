import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

load_dotenv()

security = HTTPBearer()

SECRET_KEY = os.getenv(
    "SECRET_KEY", "secreto_super_seguro"
)  # Fallback inseguro si no hay env
ALGORITHM = "HS256"


async def validar_token(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependencia de seguridad.
    Decodifica y valida el token JWT.
    """
    token_recibido = credenciales.credentials
    exception_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas. Token no válido.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token_recibido, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise exception_auth
    except jwt.InvalidTokenError:
        raise exception_auth

    return token_recibido
