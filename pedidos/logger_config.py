import logging
import os
from logging.handlers import RotatingFileHandler

def configurar_logger(nombre_servicio: str):
    """ 
    Configura un logger que escribe en consola y en archivo rotativo.
    Crea automáticamente la carpeta 'logs/ si no existe
    """

    # 1. Crear carpeta de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 2. Configurar el logger base
    logger = logging.getLogger(nombre_servicio)
    logger.setLevel(logging.INFO) # Nivel minimo para capturar

    if logger.handlers:
        return logger
    
    # 3. Definir el formato visual
    # Ejemplo: [2025-12-19 10:00:00] [PEDIDOS] [ERROR] El mensaje... 
    formato = logging.Formatter(
            fmt = "[%(asctime)s [%(name)s] [%(levelname)s] [%(message)s]",
            datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 4. Handler 1: Archivo con Rotación (Persistencia)
    # backupCount= 3 -> Guarda los ultimos 3 archivos (app.log, app.log1, app.log2)
    archivo_handler = RotatingFileHandler(
        filename=f"{log_dir}/{nombre_servicio}.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    archivo_handler.setFormatter(formato)
    logger.addHandler(archivo_handler)

    # 5. Handler 2: Consola (Para ver en tiempo real)
    consola_handler = logging.StreamHandler()
    consola_handler.setFormatter(formato)
    logger.addHandler(consola_handler)

    return logger
    