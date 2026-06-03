"""
Health check endpoints.
GET /api/health        → basic liveness, confirms the server is up.
GET /api/health/db     → confirms the Supabase connection is reachable.
"""
from fastapi import APIRouter
from datetime import datetime, timezone
from database import get_supabase
from config import settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    return {
        "status": "ok",
        "service": "baki-tracker",
        "env": settings.app_env,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/db")
def health_db():
    client = get_supabase()
    if client is None:
        return {
            "status": "not_configured",
            "message": "Supabase env vars not set yet. Add them on Railway.",
        }
    try:
        # Lightweight query: count rows in users (RLS will return 0 without auth, that's fine — connection works)
        client.table("users").select("id", count="exact").limit(1).execute()
        return {"status": "ok", "database": "reachable"}
    except Exception as e:
        return {"status": "error", "database": "unreachable", "detail": str(e)}
