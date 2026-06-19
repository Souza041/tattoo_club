from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, public, client, artist, admin
from .seed import run_seed

from fastapi import FastAPI, Response

Base.metadata.create_all(bind=engine)
run_seed()

app = FastAPI(title="Tattoo Club MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(client.router)
app.include_router(artist.router)
app.include_router(admin.router)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

if FRONTEND_DIR.exists():

    @app.get("/styles.css")
    def styles_css():
        css_file = FRONTEND_DIR / "css" / "styles.css"
        return Response(
            content=css_file.read_text(encoding="utf-8"),
            media_type="text/css"
        )

    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/")
    def root():
        return FileResponse(FRONTEND_DIR / "index.html")