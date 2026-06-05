import base64
from fastapi import Request, HTTPException
import jwt
from config import settings


def _get_jwt_key() -> bytes:
    secret = settings.supabase_jwt_secret
    try:
        return base64.b64decode(secret)
    except Exception:
        return secret.encode("utf-8")


def get_current_user(request: Request) -> str:
    """FastAPI dependency — extracts and validates the Supabase JWT.

    Returns the user's UUID (sub claim).
    Raises 401 if the token is missing, expired, or invalid.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = auth_header[7:]

    try:
        payload = jwt.decode(
            token,
            _get_jwt_key(),
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user_id
