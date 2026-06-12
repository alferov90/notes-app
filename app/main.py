import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.migrations import migrate_schema
from app.routers import auth, notes, telegram
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("noteflow")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def verify_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "notes" in tables:
        columns = {col["name"] for col in inspector.get_columns("notes")}
        if "user_id" not in columns:
            raise RuntimeError(
                "Устаревшая схема БД: в таблице notes нет колонки user_id. "
                "Выполните: docker compose down -v && docker compose up -d --build"
            )
    if "users" not in tables and "notes" in tables:
        raise RuntimeError(
            "Устаревшая схема БД: нет таблицы users. "
            "Выполните: docker compose down -v && docker compose up -d --build"
        )


def init_db(retries: int = 10, delay: float = 2.0) -> None:
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            migrate_schema()
            verify_schema()
            logger.info("Database ready")
            return
        except OperationalError as exc:
            if attempt == retries - 1:
                raise RuntimeError(
                    "Не удалось подключиться к PostgreSQL. "
                    "Проверьте DATABASE_URL и пароль в docker-compose.yml / .env"
                ) from exc
            logger.warning("DB not ready, retry %s/%s", attempt + 1, retries)
            time.sleep(delay)


init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="NoteFlow",
    description="SaaS-платформа для личных заметок",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(telegram.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


def serve_page(filename: str):
    return FileResponse(STATIC_DIR / filename)


@app.get("/")
def landing():
    return serve_page("landing.html")


@app.get("/login")
def login_page():
    return serve_page("login.html")


@app.get("/register")
def register_page():
    return serve_page("register.html")


@app.get("/app")
def notes_app():
    return serve_page("app.html")


@app.get("/dashboard")
def dashboard():
    return serve_page("dashboard.html")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
