from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    name: str
    occupation: str = ''


class UserLogin(BaseModel):
    name: str
    occupation: str = ''


class AdminLogin(BaseModel):
    email: str


class UserOut(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: str
    occupation: str = ''
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WalletOut(BaseModel):
    id: UUID
    user_id: UUID
    balance: float
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    wallet: WalletOut
