from functools import lru_cache
from typing import Union
import os
import sys # Importar sys para salir con error si las migraciones fallan

from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

# Importaciones ABSOLUTAS, asumiendo que 001-fastapi-backend/ es la raíz en Render
from database import engine, Base
from alembic.config import Config
from alembic import command

from routers import todos
import config


app = FastAPI()

app.include_router(todos.router)

origins = [
    "http://localhost:3000",
    "https://to-do-app-frontend-nextjs.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(f"HTTP Exception: {repr(exc)}") # Mensaje de depuración más claro
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@lru_cache()
def get_settings():
    return config.Settings()

def run_alembic_migrations():
    print("--- INICIANDO PROCESO DE MIGRACIONES DE ALEMBIC ---")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_script_location = os.path.join(current_dir, "alembic")
        alembic_config_path = os.path.join(current_dir, "alembic.ini")

        print(f"DEBUG: Directorio actual: {current_dir}")
        print(f"DEBUG: Ruta esperada para alembic.ini: {alembic_config_path}")
        print(f"DEBUG: Ruta esperada para directorio 'alembic': {alembic_script_location}")


        if not os.path.exists(alembic_config_path):
            print(f"ERROR CRÍTICO: alembic.ini NO ENCONTRADO en {alembic_config_path}")
            # Forzar la salida si el archivo crucial no se encuentra
            sys.exit(1)
        if not os.path.exists(alembic_script_location):
            print(f"ERROR CRÍTICO: Directorio 'alembic' NO ENCONTRADO en {alembic_script_location}")
            # Forzar la salida si el directorio crucial no se encuentra
            sys.exit(1)

        alembic_cfg = Config(alembic_config_path)
        alembic_cfg.set_main_option("script_location", alembic_script_location)

        # Aquí es donde realmente se ejecuta la migración
        print("DEBUG: Intentando llamar a command.upgrade('head')...")
        command.upgrade(alembic_cfg, "head")
        print("Migraciones de Alembic ejecutadas exitosamente.")
        print("--- FIN DEL PROCESO DE MIGRACIONES DE ALEMBIC ---")

    except Exception as e:
        print(f"*** ERROR CRÍTICO IRRECUPERABLE: Fallo durante la ejecución de migraciones de Alembic: {e} ***")
        # Imprimir el traceback completo para depuración
        import traceback
        traceback.print_exc()
        # Forzar la salida con un código de error para que Render marque el despliegue como fallido
        sys.exit(1)

@app.on_event("startup")
async def startup_event():
    print("FastAPI: Iniciando la aplicación...")
    # Llamar a la función de migraciones. Si esta función termina con sys.exit(1),
    # la aplicación no se iniciará y el despliegue de Render fallará.
    run_alembic_migrations()
    print("FastAPI: Aplicación lista.")

@app.get("/")
def read_root(settings: config.Settings = Depends(get_settings)):
    print(settings.app_name)
    return "Hello World"

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}