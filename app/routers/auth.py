from fastapi import APIRouter, HTTPException
from jose import jwt
from datetime import datetime, timedelta
from uuid import uuid4
from app.database import supabase
from app.config import settings
from app.schemas.user import UserCreate, UserLogin, AdminLogin, UserOut, WalletOut, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])
jwt_secret: str
SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        res = supabase.table("users").select("*").eq("id", user_id).execute()
        if not res.data:
            raise HTTPException(401, "User not found")
        return res.data[0]
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")


@router.post("/register", response_model=TokenOut)
def register(data: UserCreate):

    existing = (
        supabase.table("users")
        .select("id")
        .eq("full_name", data.name)
        .execute()
    )

    if existing.data:
        raise HTTPException(400, "Name already taken")

    user_id = str(uuid4())

    supabase.table("users").insert({
        "id": user_id,
        "full_name": data.name,
        "occupation": data.occupation,
    })

    supabase.table("wallets").update({"balance": 1000}).eq("user_id", user_id).execute()

    user_res = (
        supabase.table("users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )

    wallet_res = (
        supabase.table("wallets")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    token = create_token(user_id)

    return TokenOut(
        access_token=token,
        user=UserOut(**user_res.data[0]),
        wallet=WalletOut(**wallet_res.data[0]),
    )


@router.post("/login", response_model=TokenOut)
def login(data: UserLogin):
    res = supabase.table("users").select("*").eq("full_name", data.name).execute()
    if not res.data:
        raise HTTPException(401, "User not found")

    user = res.data[0]

    wallet_res = supabase.table("wallets").select("*").eq("user_id", user["id"]).execute()
    wallet_data = wallet_res.data[0] if wallet_res.data else {"balance": 0.0}
    token = create_token(user["id"])

    return TokenOut(
        access_token=token,
        user=UserOut(**user),
        wallet=WalletOut(**wallet_data),
    )


@router.post("/admin/login", response_model=TokenOut)
def admin_login(data: AdminLogin):
    res = supabase.table("users").select("*").eq("email", data.email).execute()
    if not res.data:
        raise HTTPException(401, "Invalid credentials")

    user = res.data[0]

    admin_res = supabase.table("admins").select("*").eq("user_id", user["id"]).execute()
    if not admin_res.data:
        raise HTTPException(403, "Admin access required")

    wallet_res = supabase.table("wallets").select("*").eq("user_id", user["id"]).execute()
    wallet_data = wallet_res.data[0] if wallet_res.data else {"balance": 0.0}
    token = create_token(user["id"])

    return TokenOut(
        access_token=token,
        user=UserOut(**user),
        wallet=WalletOut(**wallet_data),
    )


@router.get("/me", response_model=UserOut)
def me(token: str):
    user = get_current_user(token)
    return UserOut(**user)
