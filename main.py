from functools import lru_cache
from typing import Union
import os

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
    print(f"{repr(exc)}")
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@lru_cache()
def get_settings():
    return config.Settings()

def run_alembic_migrations():
    print("Intentando ejecutar migraciones de Alembic al iniciar la app...")
    try:
        # La ruta al directorio 'alembic' y 'alembic.ini'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_script_location = os.path.join(current_dir, "alembic")
        alembic_config_path = os.path.join(current_dir, "alembic.ini")

        if not os.path.exists(alembic_config_path):
            print(f"ERROR: alembic.ini no encontrado en {alembic_config_path}")
            raise FileNotFoundError(f"alembic.ini not found at {alembic_config_path}")
        if not os.os.path.exists(alembic_script_location): # Corregido os.os.path a os.path
            print(f"ERROR: Directorio 'alembic' no encontrado en {alembic_script_location}")
            raise FileNotFoundError(f"'alembic' directory not found at {alembic_script_location}")

        alembic_cfg = Config(alembic_config_path)
        alembic_cfg.set_main_option("script_location", alembic_script_location)

        command.upgrade(alembic_cfg, "head")
        print("Migraciones de Alembic ejecutadas exitosamente.")
    except Exception as e:
        print(f"*** ERROR CRÍTICO: Fallo al ejecutar migraciones de Alembic: {e} ***")
        raise e

@app.on_event("startup")
async def startup_event():
    print("Iniciando la aplicación FastAPI...")
    run_alembic_migrations()
    print("Aplicación FastAPI lista.")

@app.get("/")
def read_root(settings: config.Settings = Depends(get_settings)):
    print(settings.app_name)
    return "Hello World"

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}