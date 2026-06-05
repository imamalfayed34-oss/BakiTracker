"""
Health check endpoints.
GET /api/health        → basic liveness, confirms the server is up.
GET /api/health/db     → confirms the Supabase connection is reachable.
GET /api/health/jwt    → debug: test JWT decoding (TEMPORARY).
"""
from fastapi import APIRouter, Query
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


@router.get("/jwt")
def debug_jwt(token: str = Query("")):
    """TEMPORARY debug endpoint — test JWT decoding."""
    import jwt as pyjwt
    import base64

    secret_raw = settings.supabase_jwt_secret
    if not secret_raw:
        return {"error": "SUPABASE_JWT_SECRET not set", "env_keys": list(settings.model_fields.keys())}

    results = {}

    # Try as plain string
    try:
        payload = pyjwt.decode(token, secret_raw, algorithms=["HS256"], audience="authenticated")
        results["plain_string"] = {"ok": True, "sub": payload.get("sub")}
    except Exception as e:
        results["plain_string"] = {"ok": False, "error": str(e)}

    # Try base64 decoded
    try:
        key = base64.b64decode(secret_raw)
        payload = pyjwt.decode(token, key, algorithms=["HS256"], audience="authenticated")
        results["base64_decoded"] = {"ok": True, "sub": payload.get("sub")}
    except Exception as e:
        results["base64_decoded"] = {"ok": False, "error": str(e)}

    # Try without audience
    try:
        payload = pyjwt.decode(token, secret_raw, algorithms=["HS256"], options={"verify_aud": False})
        results["no_audience_check"] = {"ok": True, "sub": payload.get("sub"), "aud": payload.get("aud")}
    except Exception as e:
        results["no_audience_check"] = {"ok": False, "error": str(e)}

    return {"secret_length": len(secret_raw), "secret_starts": secret_raw[:8], "results": results}
