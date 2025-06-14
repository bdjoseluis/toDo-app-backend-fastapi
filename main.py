from functools import lru_cache
from typing import Union
import os

from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- ¡CAMBIOS EN LAS IMPORTACIONES AQUÍ! ---
# Importaciones absolutas, asumiendo que el Root Directory de Render es 001-fastapi-backend/
# y que estos archivos/directorios están directamente dentro de 001-fastapi-backend/
from database import engine, Base # Ya NO es .database
from alembic.config import Config
from alembic import command

from routers import todos # Ya NO es .routers
import config # Ya NO es .config
# --- FIN DE CAMBIOS EN LAS IMPORTACIONES ---


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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_script_location = os.path.join(current_dir, "alembic")
        alembic_config_path = os.path.join(current_dir, "alembic.ini")

        if not os.path.exists(alembic_config_path):
            print(f"ERROR: alembic.ini no encontrado en {alembic_config_path}")
            raise FileNotFoundError(f"alembic.ini not found at {alembic_config_path}")
        if not os.path.exists(alembic_script_location):
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