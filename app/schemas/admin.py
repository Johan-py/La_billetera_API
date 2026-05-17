from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class AdminCreate(BaseModel):
    user_id: UUID
    role: str = 'admin'


class AdminUserOut(BaseModel):
    id: UUID
    user_id: UUID
    role: str


class UserCreditRow(BaseModel):
    user_id: UUID
    email: Optional[str] = None
    full_name: str
    total_transactions: int
    total_volume: float
    current_balance: float
    active_savings_total: float
    passive_savings_total: float
    total_accumulated: float
    credit_score: float
    is_approved: bool
