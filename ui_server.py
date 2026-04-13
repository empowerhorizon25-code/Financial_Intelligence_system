from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fis_api import app as api_app

app = FastAPI(title="Financial Intelligence System UI")

# Always resolve paths relative to THIS file (package-safe)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/api", api_app)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav = STATIC_DIR / "favicon.ico"
    # Optional: don't crash if favicon doesn't exist
    if fav.exists():
        return FileResponse(str(fav))
    return FileResponse(str(STATIC_DIR / "index.html"))
