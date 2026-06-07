# Sistema de Microservicios E-Commerce

Este repositorio contiene una arquitectura de microservicios desarrollada con **FastAPI** para la gestión de un sistema de comercio electrónico. El sistema está dividido en servicios independientes para autenticación, productos, inventario y pedidos, comunicándose entre sí y compartiendo estándares de desarrollo.

## 🚀 Características Principales

- **Arquitectura de Microservicios**: Servicios desacoplados y escalables.
- **FastAPI**: Alto rendimiento y facilidad de desarrollo.
- **Asincronía**: Uso de `async`/`await` para operaciones I/O eficientes.
- **SQLModel & SQLAlchemy**: ORM moderno y tipado.
- **Autenticación JWT**: Seguridad centralizada en un servicio de Auth.
- **Resiliencia**: Circuit Breaker (`aiobreaker`) + Retry Policy (`tenacity`) para tolerancia a fallos.


## 🏗️ Servicios

El sistema consta de los siguientes microservicios:

1.  **Auth Service** (`/auth`): Maneja el registro y login de usuarios, emitiendo tokens JWT.
2.  **Productos Service** (`/productos`): Gestión del catálogo de productos.
3.  **Inventario Service** (`/inventario`): Control de stock y actualizaciones de inventario.
4.  **Pedidos Service** (`/pedidos`): Creación y gestión de órdenes de compra.

## 🛠️ Tecnologías

- **Lenguaje**: Python 3.10+
- **Framework Web**: FastAPI
- **Servidor**: Uvicorn
- **Base de Datos**: PostgreSQL (o SQLite para desarrollo) con AsyncPG.
- **Cliente HTTP**: HTTPX
- **Validación de Datos**: Pydantic

## 📋 Prerrequisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Base de datos (PostgreSQL recomendada)

## 🔧 Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <url-del-repositorio>
    cd 06_microservicios
    ```

2.  **Crear y activar un entorno virtual:**

    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuración de Variables de Entorno:**
    Crea un archivo `.env` en la raíz (basado en `.env.example` si existe o ver documentación en `docs/setup.md`).

## ▶️ Ejecución

Cada microservicio debe ejecutarse en un puerto distinto. Puedes abrir múltiples terminales y ejecutar:

**Servicio de Auth (Puerto 8000 - por defecto o configurar):**
```bash
uvicorn auth.main:app --port 8000 --reload
```

**Servicio de Productos (Puerto 8001):**
```bash
uvicorn productos.main:app --port 8001 --reload
```

**Servicio de Inventario (Puerto 8002):**
```bash
uvicorn inventario.main:app --port 8002 --reload
```

**Servicio de Pedidos (Puerto 8003):**
```bash
uvicorn pedidos.main:app --port 8003 --reload
```

## 📚 Documentación

Para información más detallada, consulta la carpeta `docs/`:

- [Arquitectura del Sistema](docs/architecture.md)
- [Guía de Configuración y Despliegue](docs/setup.md)
- [Referencia de API](docs/api_reference.md)

## 🐳 Docker y Docker Compose

La forma más sencilla y profesional de ejecutar todo el ecosistema (incluyendo una base de datos PostgreSQL con bases de datos lógicas individuales para cada servicio) es utilizando **Docker Compose**.

### Prerrequisitos para Docker
* Tener instalado [Docker Desktop](https://www.docker.com/products/docker-desktop/) (que incluye Docker Compose).

### Ejecutar con Docker Compose (Recomendado)

1. **Configurar el entorno**:
   Copia el archivo de plantilla `.env.example` a `.env` en la raíz del proyecto para definir las claves por defecto (opcional, Docker Compose usa valores seguros por defecto si no se define):
   ```bash
   cp .env.example .env
   ```

2. **Levantar todo el ecosistema**:
   Ejecuta el siguiente comando en la raíz del proyecto para construir las imágenes de los microservicios y levantar los contenedores en segundo plano:
   ```bash
   docker-compose up --build -d
   ```

3. **Verificar el estado de los contenedores**:
   ```bash
   docker-compose ps
   ```

4. **Acceder a los servicios**:
   Una vez levantados, puedes acceder a la documentación interactiva (Swagger UI) de cada servicio en tu navegador:
   * **Auth Service**: [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Productos Service**: [http://localhost:8001/docs](http://localhost:8001/docs)
   * **Inventario Service**: [http://localhost:8002/docs](http://localhost:8002/docs)
   * **Pedidos Service**: [http://localhost:8003/docs](http://localhost:8003/docs)

5. **Detener el entorno**:
   Para detener y eliminar los contenedores, volúmenes de datos y la red interna creada:
   ```bash
   docker-compose down -v
   ```

---

### Construir y ejecutar contenedores manualmente (Opcional - Usando SQLite)

Si prefieres no usar la base de datos PostgreSQL de Docker Compose y quieres probar los servicios de forma individual usando SQLite:

#### 1. Construir las imágenes individuales
Navega al directorio de cada servicio para construir su imagen:
```bash
# Auth
cd auth && docker build -t ecommerce-auth . && cd ..

# Productos
cd productos && docker build -t ecommerce-productos . && cd ..

# Inventario
cd inventario && docker build -t ecommerce-inventario . && cd ..

# Pedidos
cd pedidos && docker build -t ecommerce-pedidos . && cd ..
```

#### 2. Ejecutar los contenedores por separado
```bash
docker run -d --name auth-service -p 8000:8000 ecommerce-auth
docker run -d --name productos-service -p 8001:8001 ecommerce-productos
docker run -d --name inventario-service -p 8002:8002 ecommerce-inventario
docker run -d --name pedidos-service -p 8003:8003 ecommerce-pedidos
```

> **Nota**: Para que los microservicios se comuniquen entre sí manualmente sin Docker Compose, deberás configurar las variables de entorno `PRODUCTOS_SERVICE_URL` e `INVENTARIO_SERVICE_URL` apuntando al host (`http://host.docker.internal:<puerto>`) o a sus IPs respectivas.

### Detener y eliminar contenedores manuales

```bash
docker stop auth-service productos-service inventario-service pedidos-service
docker rm auth-service productos-service inventario-service pedidos-service
```

## 🤝 Contribución

1.  Haz un Fork del proyecto.
2.  Crea tu rama de funcionalidad (`git checkout -b feature/AmazingFeature`).
3.  Haz Commit de tus cambios (`git commit -m 'Add some AmazingFeature'`).
4.  Haz Push a la rama (`git push origin feature/AmazingFeature`).
5.  Abre un Pull Request.
