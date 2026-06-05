"""
Baki Tracker — FastAPI application entry point.

Serves:
  - API routes under /api/*
  - The PWA frontend (static files) for everything else

One deployment, one domain. The frontend talks to /api/* on the same origin.
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import health, auth

app = FastAPI(title="Baki Tracker", version="0.1.0")

# CORS — permissive for now; tighten to your domain before launch.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routes ---
app.include_router(health.router)
app.include_router(auth.router)

# --- Frontend (PWA) ---
# The frontend folder sits one level up from /backend.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/manifest.json")
def serve_manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json")


@app.get("/service-worker.js")
def serve_sw():
    # Served from root so its scope covers the whole site.
    return FileResponse(FRONTEND_DIR / "service-worker.js", media_type="application/javascript")


# Mount remaining static assets (css, js, icons) under /static.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
