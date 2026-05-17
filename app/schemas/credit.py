from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class CreditHistoryOut(BaseModel):
    id: UUID
    user_id: UUID
    total_transactions: int
    total_volume: float
    avg_transaction: float
    income_stability_score: float
    savings_consistency: float
    credit_score: float
    is_approved: bool
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    last_evaluated_at: datetime
    created_at: datetime
    updated_at: datetime


class CreditEvaluationOut(BaseModel):
    user_id: UUID
    credit_score: float
    is_approved: bool
    factors: dict


class AdminCreditDecision(BaseModel):
    user_id: UUID
    is_approved: bool
