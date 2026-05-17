from fastapi import APIRouter
from app.database import supabase
from app.routers.auth import get_current_user
from app.schemas.credit import CreditHistoryOut, CreditEvaluationOut
from app.services.credit import evaluate_user_credit

router = APIRouter(prefix="/credit", tags=["credit"])


@router.get("/history", response_model=CreditHistoryOut)
def get_credit_history(token: str):
    user = get_current_user(token)
    res = supabase.table("credit_histories") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .execute()

    if not res.data:
        evaluation = evaluate_user_credit(user["id"])
        res = supabase.table("credit_histories") \
            .select("*") \
            .eq("user_id", user["id"]) \
            .execute()
        if not res.data:
            return CreditHistoryOut(
                user_id=user["id"],
                credit_score=evaluation["credit_score"],
                is_approved=evaluation["is_approved"],
            )

    return CreditHistoryOut(**res.data[0])


@router.post("/evaluate", response_model=CreditEvaluationOut)
def evaluate_credit(token: str):
    user = get_current_user(token)
    result = evaluate_user_credit(user["id"])
    return CreditEvaluationOut(**result)
