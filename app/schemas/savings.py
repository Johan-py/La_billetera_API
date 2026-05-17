from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class SavingsToggle(BaseModel):
    enabled: bool
    custom_amount: Optional[float] = None


class SavingsConfigOut(BaseModel):
    id: UUID
    user_id: UUID
    active_savings_enabled: bool
    active_savings_per_tx: float
    active_savings_total: float
    passive_savings_total: float
    last_weekly_spend: float
    suggested_active_amount: float
    created_at: datetime
    updated_at: datetime


class SavingsLogOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    amount: float
    source_transaction_id: Optional[UUID] = None
    created_at: datetime


class SavingsSummary(BaseModel):
    total_saved: float
    active_savings_total: float
    passive_savings_total: float
    active_savings_enabled: bool
    active_savings_per_tx: float
    suggested_active_amount: float
