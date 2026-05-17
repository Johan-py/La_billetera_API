from app.database import supabase
from app.services.patterns import analyze_user_patterns
from typing import Optional
from uuid import UUID


def evaluate_user_credit(user_id: str) -> dict:
    patterns = analyze_user_patterns(user_id)

    existing = supabase.table("credit_histories") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()

    data = {
        "total_transactions": patterns["total_transactions"],
        "total_volume": patterns["total_volume"],
        "avg_transaction": patterns["avg_transaction"],
        "income_stability_score": patterns["income_stability_score"],
        "savings_consistency": patterns["savings_consistency"],
        "credit_score": patterns["credit_score"],
        "is_approved": patterns["is_approved"],
        "last_evaluated_at": "now",
    }

    if existing.data:
        supabase.table("credit_histories") \
            .eq("user_id", user_id) \
            .update(data)
    else:
        supabase.table("credit_histories") \
            .insert({"user_id": user_id, **data})

    return {
        "user_id": user_id,
        "credit_score": patterns["credit_score"],
        "is_approved": patterns["is_approved"],
        "factors": {
            "total_transactions": patterns["total_transactions"],
            "total_volume": patterns["total_volume"],
            "avg_transaction": patterns["avg_transaction"],
            "income_stability_score": patterns["income_stability_score"],
            "savings_consistency": patterns["savings_consistency"],
        },
    }


def admin_override_credit_decision(admin_id: str, target_user_id: str, is_approved: bool) -> dict:
    existing = supabase.table("credit_histories") \
        .select("*") \
        .eq("user_id", target_user_id) \
        .execute()

    if existing.data:
        supabase.table("credit_histories") \
            .eq("user_id", target_user_id) \
            .update({
                "is_approved": is_approved,
                "approved_by": admin_id,
                "approved_at": "now",
            })
    else:
        supabase.table("credit_histories") \
            .insert({
                "user_id": target_user_id,
                "is_approved": is_approved,
                "approved_by": admin_id,
                "approved_at": "now",
            })

    return {"user_id": target_user_id, "is_approved": is_approved, "overridden_by": admin_id}
