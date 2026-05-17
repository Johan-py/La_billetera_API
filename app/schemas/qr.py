from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class QrPaymentCreate(BaseModel):
    amount: float
    description: str = ""

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class QrPaymentStatusOut(BaseModel):
    id: UUID
    amount: float
    description: str
    status: str
    to_user_name: str
    to_user_id: UUID
    expires_at: datetime


class QrPaymentGenerateOut(BaseModel):
    id: UUID
    amount: float
    description: str
    status: str
    to_user: dict
    expires_at: datetime


class QrPaymentPayOut(BaseModel):
    transaction: dict
    new_balance: float
    to_user: str
    savings_applied: dict
