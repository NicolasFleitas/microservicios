# Sistema de Microservicios E-Commerce

Arquitectura de microservicios con **FastAPI** para un sistema de comercio electrónico: autenticación, productos, inventario y pedidos como servicios independientes. La forma recomendada de ejecutarlo es con **Docker Compose**, que levanta los cuatro servicios y PostgreSQL con un solo comando.

## Vía rápida: Docker Compose

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (incluye Docker Compose v2).

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Verificación: la documentación interactiva (Swagger UI) de cada servicio responde en el navegador:

| Servicio | URL |
|----------|-----|
| Auth | http://localhost:8000/docs |
| Productos | http://localhost:8001/docs |
| Inventario | http://localhost:8002/docs |
| Pedidos | http://localhost:8003/docs |

Para detener y eliminar contenedores, volúmenes y red interna:

```bash
docker compose down -v
```

## Detalles

| Tema | Decisión |
|------|----------|
| Orquestación | Docker Compose v2 (`docker compose`, sin guion) levanta Postgres + 4 servicios |
| Base de datos | PostgreSQL con una base lógica por servicio, creadas por `init-dbs.sql` |
| Puertos | 8000 (auth), 8001 (productos), 8002 (inventario), 8003 (pedidos), 5432 (Postgres) |
| Salud de Postgres | `healthcheck` con `pg_isready`; los servicios esperan a que esté sana (`service_healthy`) |
| Variables de entorno | Compose ya las conecta (`SECRET_KEY`, `*_DB_URL`, `PRODUCTOS_SERVICE_URL`, `INVENTARIO_SERVICE_URL`); `.env` es opcional con valores por defecto seguros |
| Dependencias Python | No hay `requirements.txt` en la raíz; cada servicio tiene el suyo (`auth/requirements.txt`, etc.) |

## Servicios

| Servicio | Código | Puerto |
|----------|--------|--------|
| Auth (registro, login, JWT) | `auth/main.py` (`app`) | 8000 |
| Productos (catálogo) | `productos/main.py` (`app`) | 8001 |
| Inventario (stock) | `inventario/main.py` (`app`) | 8002 |
| Pedidos (órdenes) | `pedidos/main.py` (`app`) | 8003 |

## Tecnologías

Python 3.10+, FastAPI, Uvicorn, PostgreSQL (AsyncPG), SQLModel / SQLAlchemy, Pydantic, HTTPX, autenticación JWT, resiliencia con Circuit Breaker (`aiobreaker`) y reintentos (`tenacity`).

## Documentación

- [Arquitectura del Sistema](docs/architecture.md)
- [Guía de Configuración y Despliegue](docs/setup.md)
- [Referencia de API](docs/api_reference.md)

## Lista de verificación

- [ ] `docker compose ps` muestra los 5 contenedores en ejecución
- [ ] Cada `/docs` responde en su puerto (8000–8003)
- [ ] `docs/` y `.env.example` existen como referencia

## Siguiente paso

En GitHub Codespaces el archivo `.devcontainer/devcontainer.json` levanta el stack automáticamente (`postStartCommand`) y reenvía los puertos 8000–8003 y 5432 al panel **PORTS**. Abrir cada servicio con la URL del codespace, por ejemplo `https://<codespace>-8000.app.github.dev/docs`.

<details>
<summary>Desarrollo avanzado sin Compose (venv + uvicorn por servicio)</summary>

Desde la raíz del repositorio, instalar las dependencias de cada servicio y ejecutarlo en terminales separadas:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r auth/requirements.txt
pip install -r productos/requirements.txt
pip install -r inventario/requirements.txt
pip install -r pedidos/requirements.txt
```

```bash
uvicorn auth.main:app --port 8000 --reload
uvicorn productos.main:app --port 8001 --reload
uvicorn inventario.main:app --port 8002 --reload
uvicorn pedidos.main:app --port 8003 --reload
```

Fuera de Compose es necesario definir manualmente las variables que Compose ya conecta: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, las URL de base de datos (`AUTH_DB_URL`, `PRODUCTOS_DB_URL`, `INVENTARIO_DB_URL`, `PEDIDOS_DB_URL`) y las URL entre servicios (`PRODUCTOS_SERVICE_URL`, `INVENTARIO_SERVICE_URL`). Ver los valores exactos en `docker-compose.yml`.

</details>

<details>
<summary>Construcción manual de imágenes Docker (avanzado)</summary>

Cada servicio tiene su propio `Dockerfile` con contexto en su directorio:

```bash
cd auth && docker build -t ecommerce-auth . && cd ..
cd productos && docker build -t ecommerce-productos . && cd ..
cd inventario && docker build -t ecommerce-inventario . && cd ..
cd pedidos && docker build -t ecommerce-pedidos . && cd ..
```

```bash
docker run -d --name auth-service -p 8000:8000 ecommerce-auth
docker run -d --name productos-service -p 8001:8001 ecommerce-productos
docker run -d --name inventario-service -p 8002:8002 ecommerce-inventario
docker run -d --name pedidos-service -p 8003:8003 ecommerce-pedidos
```

> Nota: sin Docker Compose, configurar `PRODUCTOS_SERVICE_URL` e `INVENTARIO_SERVICE_URL` hacia el host correspondiente. Para detener: `docker stop auth-service productos-service inventario-service pedidos-service` y `docker rm` con los mismos nombres.

</details>

## Contribución

1. Crear una rama (`git checkout -b feature/NuevaFuncionalidad`).
2. Registrar los cambios (`git commit -m 'Add some NuevaFuncionalidad'`).
3. Publicar la rama (`git push origin feature/NuevaFuncionalidad`).
4. Abrir un Pull Request.
