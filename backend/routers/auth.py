from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from database import get_supabase, get_supabase_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ProfileCreate(BaseModel):
    shop_name: str


@router.get("/me")
def get_profile(user_id: str = Depends(get_current_user)):
    client = get_supabase()
    if client is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    result = client.table("users").select("*").eq("id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return result.data[0]


@router.post("/profile", status_code=201)
def create_profile(body: ProfileCreate, user_id: str = Depends(get_current_user)):
    client = get_supabase_service()
    if client is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    existing = client.table("users").select("id").eq("id", user_id).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Profile already exists")

    user_response = client.auth.admin.get_user_by_id(user_id)
    phone = user_response.user.phone or ""

    result = client.table("users").insert({
        "id": user_id,
        "phone": phone,
        "shop_name": body.shop_name,
    }).execute()

    return result.data[0]
