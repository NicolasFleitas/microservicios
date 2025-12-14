# Referencia de API y Flujos de Trabajo

Esta sección documenta los endpoints principales y ejemplos de flujos de trabajo comunes. Recuerda que cada microservicio expone su propia documentación interactiva en `/docs` (Swagger UI) y `/redoc`.

## Autenticación

Todos los endpoints protegidos requieren un token JWT en el encabezado `Authorization`.

**Formato:**
```http
Authorization: Bearer <tu_token_access_token>
```

## Resumen de Endpoints

### Auth Service (:8000)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/register` | Registra un nuevo usuario en el sistema. |
| POST | `/login` | Valida credenciales y devuelve un `access_token`. |

### Productos Service (:8001)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/productos` | Lista todos los productos disponibles. |
| POST | `/productos` | Crea un nuevo producto. |
| GET | `/productos/{id}` | Obtiene detalles de un producto específico. |
| PATCH | `/productos/{id}` | Actualiza información de un producto. |

### Inventario Service (:8002)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/inventario` | Lista el stock de todos los items. |
| POST | `/inventario` | Registra stock inicial para un producto. |
| GET | `/inventario/{id}` | Verifica el stock de un producto específico. |
| PATCH | `/inventario/{id}` | Actualiza el stock (manual o por sistema). |

### Pedidos Service (:8003)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/pedidos` | Crea una orden de compra. Valida stock y producto. |
| GET | `/pedidos` | Lista los pedidos del usuario/sistema. |
| PATCH | `/pedidos/{id}` | Modifica el estado de un pedido. |

---

## Flujo de Trabajo: Crear un Pedido

Este es el flujo típico para realizar un pedido en el sistema (el proceso de pago se gestionará en un futuro microservicio):

1.  **Login**:
    El usuario (o frontend) envía credenciales a `POST :8000/login`.
    - *Respuesta*: `{ "access_token": "eyJhb...", "token_type": "bearer" }`

2.  **Consultar Productos (Opcional)**:
    El usuario consulta el catálogo en `GET :8001/productos` para obtener el ID del producto deseado.

3.  **Realizar Pedido**:
    El usuario envía una petición a `POST :8003/pedidos` con el Header `Authorization: Bearer ...`.
    
    **Body:**
    ```json
    {
      "producto_id": 1,
      "cantidad": 5
    }
    ```

    **Proceso Interno (Orquestación):**
    - `Pedidos` verifica el token.
    - `Pedidos` llama internamente a `Inventario` para verificar si hay stock suficiente.
    - `Pedidos` guarda el pedido en su BD con estado "Pendiente".
    - `Pedidos` llama a `Inventario` para descontar el stock.
    - *Respuesta*: Confirmación del pedido y detalles del mismo.