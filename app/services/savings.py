from app.database import supabase
from datetime import datetime, timedelta


def calculate_weekly_spend(user_id: str) -> float:
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    res = supabase.table("transactions") \
        .select("amount") \
        .eq("user_id", user_id) \
        .eq("type", "expense") \
        .gte("created_at", week_ago) \
        .execute()
    return sum(tx["amount"] for tx in res.data)


def suggest_active_savings_amount(weekly_spend: float) -> float:
    if weekly_spend <= 0:
        return 0.0
    suggested = round(weekly_spend * 0.01, 2)
    return max(suggested, 0.50)


def apply_passive_savings(amount: float) -> float:
    decimal_part = amount - int(amount)
    if decimal_part > 0:
        return round(1.0 - decimal_part, 2)
    return 0.0


def process_savings_on_transaction(user_id: str, transaction_id: str, amount: float):
    savings_res = supabase.table("savings_configs") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()

    if not savings_res.data:
        weekly = calculate_weekly_spend(user_id)
        suggested = suggest_active_savings_amount(weekly)
        supabase.table("savings_configs").insert({
            "user_id": user_id,
            "last_weekly_spend": weekly,
            "suggested_active_amount": suggested,
        })
        savings_res = supabase.table("savings_configs") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

    savings = savings_res.data[0]

    passive_amount = apply_passive_savings(amount)
    if passive_amount > 0:
        supabase.table("savings_logs").insert({
            "user_id": user_id,
            "type": "passive",
            "amount": passive_amount,
            "source_transaction_id": transaction_id,
        })
        supabase.table("savings_configs") \
            .eq("user_id", user_id) \
            .update({"passive_savings_total": round(savings["passive_savings_total"] + passive_amount, 2)})

    active_amount = 0.0
    if savings.get("active_savings_enabled"):
        active_amount = savings.get("active_savings_per_tx", 0.0)
        if active_amount > 0:
            supabase.table("savings_logs").insert({
                "user_id": user_id,
                "type": "active",
                "amount": active_amount,
                "source_transaction_id": transaction_id,
            })
            supabase.table("savings_configs") \
                .eq("user_id", user_id) \
                .update({"active_savings_total": round(savings["active_savings_total"] + active_amount, 2)})

    weekly = calculate_weekly_spend(user_id)
    suggested = suggest_active_savings_amount(weekly)
    supabase.table("savings_configs") \
        .eq("user_id", user_id) \
        .update({
            "last_weekly_spend": weekly,
            "suggested_active_amount": suggested,
        })

    return {
        "passive_saved": passive_amount,
        "active_saved": active_amount,
    }
