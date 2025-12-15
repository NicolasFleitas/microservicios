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

## 🤝 Contribución

1.  Haz un Fork del proyecto.
2.  Crea tu rama de funcionalidad (`git checkout -b feature/AmazingFeature`).
3.  Haz Commit de tus cambios (`git commit -m 'Add some AmazingFeature'`).
4.  Haz Push a la rama (`git push origin feature/AmazingFeature`).
5.  Abre un Pull Request.
