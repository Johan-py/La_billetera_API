from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.database import supabase
from app.routers.auth import get_current_user
from app.schemas.qr import (
    QrPaymentCreate,
    QrPaymentStatusOut,
    QrPaymentGenerateOut,
    QrPaymentPayOut,
)
from app.services.savings import process_savings_on_transaction


router = APIRouter(prefix="/qr", tags=["qr"])


@router.post("/generate", response_model=QrPaymentGenerateOut)
def generate_qr(data: QrPaymentCreate, token: str):
    user = get_current_user(token)
    user_id = user["id"]

    payment_id = str(uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    supabase.table("qr_payments").insert({
        "id": payment_id,
        "to_user_id": user_id,
        "amount": data.amount,
        "description": data.description,
        "status": "pending",
        "expires_at": expires_at,
    })

    return QrPaymentGenerateOut(
        id=payment_id,
        amount=data.amount,
        description=data.description,
        status="pending",
        to_user={"id": user["id"], "full_name": user["full_name"]},
        expires_at=expires_at,
    )


@router.get("/{payment_id}", response_model=QrPaymentStatusOut)
def get_qr_payment(payment_id: str, token: str):
    user = get_current_user(token)

    res = supabase.table("qr_payments").select("*").eq("id", payment_id).execute()
    if not res.data:
        raise HTTPException(404, "QR payment not found")

    payment = res.data[0]

    if payment["status"] != "pending":
        raise HTTPException(400, f"Payment already {payment['status']}")

    expires_at = datetime.fromisoformat(
        payment["expires_at"].replace("Z", "+00:00")
    )
    if datetime.now(timezone.utc) > expires_at:
        supabase.table("qr_payments").eq("id", payment_id).update({
            "status": "expired"
        })
        raise HTTPException(400, "QR code expired")

    to_user_res = (
        supabase.table("users")
        .select("id, full_name")
        .eq("id", payment["to_user_id"])
        .execute()
    )
    to_user = to_user_res.data[0] if to_user_res.data else {"full_name": "Unknown"}

    return QrPaymentStatusOut(
        id=payment["id"],
        amount=payment["amount"],
        description=payment["description"],
        status=payment["status"],
        to_user_name=to_user["full_name"],
        to_user_id=payment["to_user_id"],
        expires_at=payment["expires_at"],
    )


@router.post("/pay/{payment_id}", response_model=QrPaymentPayOut)
def pay_qr(payment_id: str, token: str):
    user = get_current_user(token)
    from_user_id = user["id"]

    res = supabase.table("qr_payments").select("*").eq("id", payment_id).execute()
    if not res.data:
        raise HTTPException(404, "QR payment not found")

    payment = res.data[0]

    if payment["status"] != "pending":
        raise HTTPException(400, f"Payment already {payment['status']}")

    if payment["to_user_id"] == from_user_id:
        raise HTTPException(400, "Cannot pay yourself")

    expires_at = datetime.fromisoformat(
        payment["expires_at"].replace("Z", "+00:00")
    )
    if datetime.now(timezone.utc) > expires_at:
        supabase.table("qr_payments").eq("id", payment_id).update({
            "status": "expired"
        })
        raise HTTPException(400, "QR code expired")

    amount = payment["amount"]

    wallet_res = (
        supabase.table("wallets")
        .select("balance")
        .eq("user_id", from_user_id)
        .execute()
    )
    current_balance = wallet_res.data[0]["balance"] if wallet_res.data else 0.0

    if current_balance < amount:
        raise HTTPException(400, "Insufficient funds")

    new_payer_balance = current_balance - amount
    supabase.table("wallets").eq("user_id", from_user_id).update({
        "balance": new_payer_balance
    })

    to_wallet_res = (
        supabase.table("wallets")
        .select("balance")
        .eq("user_id", payment["to_user_id"])
        .execute()
    )
    to_balance = to_wallet_res.data[0]["balance"] if to_wallet_res.data else 0.0
    new_to_balance = to_balance + amount
    supabase.table("wallets").eq("user_id", payment["to_user_id"]).update({
        "balance": new_to_balance
    })

    payer_tx_id = str(uuid4())
    supabase.table("transactions").insert({
        "id": payer_tx_id,
        "user_id": from_user_id,
        "type": "expense",
        "amount": amount,
        "description": f"QR: {payment['description'] or 'Pago QR'}",
        "category": "Transferencia",
        "reference_id": payment_id,
    })

    receiver_tx_id = str(uuid4())
    supabase.table("transactions").insert({
        "id": receiver_tx_id,
        "user_id": payment["to_user_id"],
        "type": "income",
        "amount": amount,
        "description": f"QR: {payment['description'] or 'Cobro QR'}",
        "category": "Transferencia",
        "reference_id": payment_id,
    })

    supabase.table("qr_payments").eq("id", payment_id).update({
        "status": "completed",
        "from_user_id": from_user_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    savings_result = process_savings_on_transaction(
        from_user_id, payer_tx_id, amount
    )

    return QrPaymentPayOut(
        transaction={
            "id": payer_tx_id,
            "type": "expense",
            "amount": amount,
            "description": payment["description"] or "Pago QR",
        },
        new_balance=new_payer_balance,
        to_user=user["full_name"],
        savings_applied=savings_result,
    )


@router.get("/my/info")
def my_info(token: str):
    user = get_current_user(token)
    wallet_res = (
        supabase.table("wallets")
        .select("balance")
        .eq("user_id", user["id"])
        .execute()
    )
    balance = wallet_res.data[0]["balance"] if wallet_res.data else 0.0

    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "balance": balance,
    }
