from fastapi import APIRouter, Query
from app.database import supabase
from app.routers.auth import get_current_user
from app.schemas.savings import SavingsToggle, SavingsConfigOut, SavingsLogOut, SavingsSummary
from app.services.savings import calculate_weekly_spend, suggest_active_savings_amount

router = APIRouter(prefix="/savings", tags=["savings"])


@router.get("/config", response_model=SavingsConfigOut)
def get_savings_config(token: str):
    user = get_current_user(token)
    res = supabase.table("savings_configs") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .execute()

    if not res.data:
        weekly = calculate_weekly_spend(user["id"])
        suggested = suggest_active_savings_amount(weekly)
        supabase.table("savings_configs").insert({
            "user_id": user["id"],
            "last_weekly_spend": weekly,
            "suggested_active_amount": suggested,
        })
        res = supabase.table("savings_configs").select("*").eq("user_id", user["id"]).execute()

    return SavingsConfigOut(**res.data[0])


@router.post("/toggle", response_model=SavingsConfigOut)
def toggle_active_savings(data: SavingsToggle, token: str):
    user = get_current_user(token)
    amount = data.custom_amount

    if data.enabled and not amount:
        weekly = calculate_weekly_spend(user["id"])
        amount = suggest_active_savings_amount(weekly)

    supabase.table("savings_configs") \
        .eq("user_id", user["id"]) \
        .update({
            "active_savings_enabled": data.enabled,
            "active_savings_per_tx": amount or 0.0,
        })

    res = supabase.table("savings_configs").select("*").eq("user_id", user["id"]).execute()
    return SavingsConfigOut(**res.data[0])


@router.get("/summary", response_model=SavingsSummary)
def savings_summary(token: str):
    user = get_current_user(token)
    res = supabase.table("savings_configs") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .execute()

    if not res.data:
        return SavingsSummary()

    s = res.data[0]
    return SavingsSummary(
        total_saved=s["active_savings_total"] + s["passive_savings_total"],
        active_savings_total=s["active_savings_total"],
        passive_savings_total=s["passive_savings_total"],
        active_savings_enabled=s["active_savings_enabled"],
        active_savings_per_tx=s["active_savings_per_tx"],
        suggested_active_amount=s["suggested_active_amount"],
    )


@router.get("/log", response_model=list[SavingsLogOut])
def savings_log(
    token: str,
    limit: int = Query(50, le=100),
):
    user = get_current_user(token)
    res = supabase.table("savings_logs") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return [SavingsLogOut(**log) for log in res.data]
