from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from uuid import uuid4

from app.database import supabase
from app.routers.auth import get_current_user
from app.schemas.transaction import (
    TransactionCreate,
    TransactionOut,
    TransactionSummary,
)
from app.services.savings import process_savings_on_transaction


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


@router.post("", response_model=dict)
def create_transaction(
    data: TransactionCreate,
    token: str
):

    user = get_current_user(token)
    user_id = user["id"]

    # obtener balance actual
    wallet_res = (
        supabase.table("wallets")
        .select("balance")
        .eq("user_id", user_id)
        .execute()
    )

    current_balance = (
        wallet_res.data[0]["balance"]
        if wallet_res.data
        else 0.0
    )

    # validar fondos
    if data.type == "expense":

        if current_balance < data.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient funds"
            )

        new_balance = (
            current_balance
            - data.amount
        )

    else:

        new_balance = (
            current_balance
            + data.amount
        )

    tx_id = str(uuid4())

    # OJO: SIN execute()
    supabase.table("transactions").insert({
        "id": tx_id,
        "user_id": user_id,
        "type": data.type,
        "amount": data.amount,
        "description": data.description,
        "category": data.category,
    })

    # OJO: SIN execute()
    supabase.table("wallets")\
        .eq("user_id", user_id)\
        .update({
            "balance": new_balance
        })

    savings_result = (
        process_savings_on_transaction(
            user_id,
            tx_id,
            data.amount
        )
    )

    tx_res = (
        supabase.table("transactions")
        .select("*")
        .eq("id", tx_id)
        .execute()
    )

    transaction = TransactionOut(
        **tx_res.data[0]
    )

    return {
        "transaction": transaction.model_dump(),
        "new_balance": new_balance,
        "savings_applied": savings_result,
    }

@router.get("", response_model=list[TransactionOut])
def list_transactions(token: str):

    user = get_current_user(token)
    user_id = user["id"]

    res = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [TransactionOut(**tx) for tx in res.data]


@router.get(
    "/summary",
    response_model=TransactionSummary
)
def transaction_summary(
    token: str
):

    user = get_current_user(token)
    user_id = user["id"]

    res = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    total_income = sum(
        tx["amount"]
        for tx in res.data
        if tx["type"] == "income"
    )

    total_expense = sum(
        tx["amount"]
        for tx in res.data
        if tx["type"] == "expense"
    )

    wallet_res = (
        supabase.table("wallets")
        .select("balance")
        .eq("user_id", user_id)
        .execute()
    )

    balance = (
        wallet_res.data[0]["balance"]
        if wallet_res.data
        else 0.0
    )

    return TransactionSummary(
        total_income=total_income,
        total_expense=total_expense,
        total_transactions=len(
            res.data
        ),
        balance=balance,
    )