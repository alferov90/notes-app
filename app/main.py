import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app.database import Base, engine
from app.routers import auth, notes

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def init_db(retries: int = 10, delay: float = 2.0) -> None:
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


init_db()

app = FastAPI(
    title="NoteFlow",
    description="SaaS-платформа для личных заметок",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.include_router(auth.router)
app.include_router(notes.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
def health():
    return {"status": "ok"}
