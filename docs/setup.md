# Guía de Configuración y Despliegue

Esta guía detalla los pasos necesarios para configurar el entorno de desarrollo y ejecutar los microservicios localmente.

## 1. Configuración de Variables de Entorno

El sistema utiliza archivos `.env` para manejar la configuración sensible. Crea un archivo `.env` en el directorio raíz (`06_microservicios/`) con las siguientes variables.

> **Nota**: Asegúrate de que los puertos de base de datos coincidan con tu configuración local.

```ini
# Configuración General
SECRET_KEY=tu_clave_secreta_super_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Bases de Datos (Ejemplo con PostgreSQL)
# Formato: postgresql+asyncpg://user:password@host:port/dbname

# Base de datos Auth
DATABASE_URL_AUTH=postgresql+asyncpg://postgres:password@localhost:5432/tienda_auth

# Base de datos Productos
DATABASE_URL_PRODUCTOS=postgresql+asyncpg://postgres:password@localhost:5432/tienda_productos

# Base de datos Inventario
DATABASE_URL_INVENTARIO=postgresql+asyncpg://postgres:password@localhost:5432/tienda_inventario

# Base de datos Pedidos
DATABASE_URL_PEDIDOS=postgresql+asyncpg://postgres:password@localhost:5432/tienda_pedidos

# URLs de Servicios (Para comunicación entre ellos)
AUTH_SERVICE_URL=http://localhost:8000
PRODUCTOS_SERVICE_URL=http://localhost:8001
INVENTARIO_SERVICE_URL=http://localhost:8002
PEDIDOS_SERVICE_URL=http://localhost:8003
```

## 2. Bases de Datos

El sistema está diseñado para funcionar con **PostgreSQL**. Antes de iniciar los servicios, debes asegurarte de que:

1.  El servidor PostgreSQL esté corriendo.
2.  Las bases de datos existan (`tienda_auth`, `tienda_productos`, etc.).

Puedes crearlas usando `psql` o una herramienta como pgAdmin:

```sql
CREATE DATABASE tienda_auth;
CREATE DATABASE tienda_productos;
CREATE DATABASE tienda_inventario;
CREATE DATABASE tienda_pedidos;
```

*Nota: Los microservicios utilizan SQLModel/SQLAlchemy e intentarán crear las tablas automáticamente al iniciarse (`init_db`), pero la base de datos en sí debe existir previamente.*

## 3. Instalación de Dependencias

Asegúrate de estar en el directorio raíz y tener tu entorno virtual activo:

```bash
pip install -r requirements.txt
```

## 4. Ejecución en Desarrollo

Para ejecutar todos los servicios simultáneamente, se recomienda abrir múltiples terminales (o pestañas de terminal) y correr cada servicio en su puerto asignado:

**Terminal 1: Auth**
```bash
uvicorn auth.main:app --port 8000 --reload
```

**Terminal 2: Productos**
```bash
uvicorn productos.main:app --port 8001 --reload
```

**Terminal 3: Inventario**
```bash
uvicorn inventario.main:app --port 8002 --reload
```

**Terminal 4: Pedidos**
```bash
uvicorn pedidos.main:app --port 8003 --reload
```

Una vez iniciados, puedes acceder a la documentación interactiva (Swagger UI) de cada servicio en:
- `http://localhost:8000/docs`
- `http://localhost:8001/docs`
- `http://localhost:8002/docs`
- `http://localhost:8003/docs`
