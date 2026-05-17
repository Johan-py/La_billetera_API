from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.routers.auth import get_current_user
from app.schemas.admin import AdminUserOut, UserCreditRow
from app.services.credit import admin_override_credit_decision
from typing import Optional

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(token: str) -> dict:
    user = get_current_user(token)
    admin_res = supabase.table("admins") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .execute()
    if not admin_res.data:
        raise HTTPException(403, "Admin access required")
    return admin_res.data[0]


@router.post("/users", response_model=AdminUserOut)
def create_admin(data: dict, token: str):
    require_admin(token)
    existing = supabase.table("admins").select("*").eq("user_id", data["user_id"]).execute()
    if existing.data:
        return AdminUserOut(**existing.data[0])
    res = supabase.table("admins").insert(data)
    return AdminUserOut(**res.data[0])


@router.get("/users", response_model=list[UserCreditRow])
def list_users_with_credit(token: str, search: Optional[str] = None):
    require_admin(token)
    res = supabase.table("admin_user_financials") \
        .select("*") \
        .order("user_id") \
        .execute()
    result = [UserCreditRow(**row) for row in res.data]
    if search:
        result = [
            r for r in result
            if search.lower() in (r.email or "").lower()
            or search.lower() in r.full_name.lower()
        ]
    return result


@router.post("/credit/decision", response_model=dict)
def override_credit_decision(data: dict, token: str):
    admin = require_admin(token)
    target_user_id = data.get("user_id")
    is_approved = data.get("is_approved", False)
    if not target_user_id:
        raise HTTPException(400, "user_id is required")
    result = admin_override_credit_decision(admin["id"], target_user_id, is_approved)
    return result


@router.get("/users/{user_id}", response_model=UserCreditRow)
def get_user_detail(user_id: str, token: str):
    require_admin(token)
    res = supabase.table("admin_user_financials") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
    if not res.data:
        raise HTTPException(404, "User not found")
    return UserCreditRow(**res.data[0])
