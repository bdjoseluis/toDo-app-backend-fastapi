from functools import lru_cache
from typing import Union
import os # Importar el módulo os para manejar rutas

from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

# Importa database y models para el startup event
from .database import engine, Base # Asume que tienes estos en database.py
from alembic.config import Config
from alembic import command

# routers: comment out next line till create them
from .routers import todos # Asegúrate que la importación sea relativa si main.py está en un subdirectorio

import config # Asume que config.py está en el mismo nivel

app = FastAPI()

# router: comment out next line till create it
app.include_router(todos.router)


origins = [
    "http://localhost:3000",
    #"https://todo-frontend-khaki.vercel.app/",
    "https://to-do-app-frontend-nextjs.vercel.app"
]

# CORS configuration, needed for frontend development
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# global http exception handler, to handle errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(f"{repr(exc)}")
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

# to use the settings
@lru_cache()
def get_settings():
    return config.Settings()


# --- ¡NUEVO CÓDIGO AQUÍ PARA MIGRACIONES! ---
# Función para ejecutar migraciones de Alembic programáticamente
def run_alembic_migrations():
    print("Intentando ejecutar migraciones de Alembic al iniciar la app...")
    try:
        # La ruta al directorio 'alembic' y 'alembic.ini'
        # Si main.py está en '001-fastapi-backend/' y 'alembic/' y 'alembic.ini' también
        # están en '001-fastapi-backend/', entonces las rutas relativas son:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_script_location = os.path.join(current_dir, "alembic")
        alembic_config_path = os.path.join(current_dir, "alembic.ini")

        # Verifica si los archivos/directorios existen
        if not os.path.exists(alembic_config_path):
            print(f"ERROR: alembic.ini no encontrado en {alembic_config_path}")
            raise FileNotFoundError(f"alembic.ini not found at {alembic_config_path}")
        if not os.path.exists(alembic_script_location):
            print(f"ERROR: Directorio 'alembic' no encontrado en {alembic_script_location}")
            raise FileNotFoundError(f"'alembic' directory not found at {alembic_script_location}")


        alembic_cfg = Config(alembic_config_path)
        alembic_cfg.set_main_option("script_location", alembic_script_location)
        # Opcional: Si tienes un env.py complejo y necesitas más configuración
        # alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL")) # Asegúrate que tu DB URL está en las variables de entorno de Render


        command.upgrade(alembic_cfg, "head")
        print("Migraciones de Alembic ejecutadas exitosamente.")
    except Exception as e:
        print(f"*** ERROR CRÍTICO: Fallo al ejecutar migraciones de Alembic: {e} ***")
        # Es crucial que la app no inicie si las migraciones fallan.
        # En un entorno de producción, podrías querer registrar esto y salir de forma elegante.
        raise e # Relanzar la excepción para que el despliegue falle si esto no funciona.

# Evento de startup de FastAPI
@app.on_event("startup")
async def startup_event():
    print("Iniciando la aplicación FastAPI...")
    # Ejecuta las migraciones antes de que la aplicación esté lista para servir peticiones
    run_alembic_migrations()
    # Si usas Base.metadata.create_all para crear tablas, puedes llamarlo aquí,
    # pero si usas Alembic, normalmente no es necesario para las tablas versionadas.
    # Base.metadata.create_all(bind=engine) # Descomentar solo si lo necesitas además de Alembic
    print("Aplicación FastAPI lista.")
# --- FIN DEL NUEVO CÓDIGO ---


@app.get("/")
def read_root(settings: config.Settings = Depends(get_settings)):
    # print the app_name configuration
    print(settings.app_name)
    return "Hello World"


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}