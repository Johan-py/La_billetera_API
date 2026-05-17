from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class TransactionCreate(BaseModel):
    type: Literal['income', 'expense', 'transfer']
    amount: float
    description: str = ''
    category: str = ''

    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('amount must be positive')
        return v


class TransactionOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    amount: float
    description: str
    category: str
    reference_id: Optional[UUID] = None
    created_at: datetime


class TransactionSummary(BaseModel):
    total_income: float = 0.0
    total_expense: float = 0.0
    total_transactions: int = 0
    balance: float = 0.0
