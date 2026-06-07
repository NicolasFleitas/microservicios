# Imagen base de Python
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias del servicio
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY . ./pedidos/

# Exponer el puerto del servicio
EXPOSE 8003

# Comando para ejecutar el servicio
CMD ["uvicorn", "pedidos.main:app", "--host", "0.0.0.0", "--port", "8003"]
