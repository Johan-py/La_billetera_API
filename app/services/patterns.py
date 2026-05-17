from app.database import supabase
from datetime import datetime, timedelta
from typing import Optional


def analyze_user_patterns(user_id: str) -> dict:
    now = datetime.utcnow()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    ninety_days_ago = (now - timedelta(days=90)).isoformat()

    tx_90 = supabase.table("transactions") \
        .select("*") \
        .eq("user_id", user_id) \
        .gte("created_at", ninety_days_ago) \
        .order("created_at", desc=True) \
        .execute()
    transactions = tx_90.data

    total_tx = len(transactions)
    if total_tx == 0:
        return {
            "total_transactions": 0,
            "total_volume": 0.0,
            "avg_transaction": 0.0,
            "income_stability_score": 0.0,
            "savings_consistency": 0.0,
            "credit_score": 0.0,
            "is_approved": False,
        }

    incomes = [t for t in transactions if t["type"] == "income"]
    expenses = [t for t in transactions if t["type"] == "expense"]

    total_volume = sum(t["amount"] for t in transactions)
    avg_transaction = round(total_volume / total_tx, 2)

    monthly_income = sum(t["amount"] for t in incomes)
    monthly_expense = sum(t["amount"] for t in expenses)

    income_stability = _calculate_income_stability(incomes, thirty_days_ago)
    savings_consistency = _calculate_savings_consistency(user_id)
    debt_ratio = _calculate_debt_ratio(monthly_income, monthly_expense)

    credit_score = _calculate_credit_score(
        total_tx, total_volume, income_stability,
        savings_consistency, debt_ratio, monthly_income
    )

    is_approved = credit_score >= 60.0

    return {
        "total_transactions": total_tx,
        "total_volume": round(total_volume, 2),
        "avg_transaction": avg_transaction,
        "income_stability_score": round(income_stability, 2),
        "savings_consistency": round(savings_consistency, 2),
        "credit_score": round(credit_score, 2),
        "is_approved": is_approved,
    }


def _calculate_income_stability(incomes: list, thirty_days_ago: str) -> float:
    if len(incomes) < 2:
        return 20.0

    recent_incomes = [t for t in incomes if t["created_at"] >= thirty_days_ago]
    if not recent_incomes:
        return 30.0

    amounts = [t["amount"] for t in recent_incomes]
    avg = sum(amounts) / len(amounts)
    if avg == 0:
        return 20.0

    variance = sum((a - avg) ** 2 for a in amounts) / len(amounts)
    cv = (variance ** 0.5) / avg

    score = max(0, 100 - (cv * 50))
    return min(100, score)


def _calculate_savings_consistency(user_id: str) -> float:
    logs = supabase.table("savings_logs") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(30) \
        .execute()

    if not logs.data:
        return 0.0

    savings_days = len(set(
        log["created_at"][:10] for log in logs.data
    ))

    score = min(100, savings_days * 10)
    return score


def _calculate_debt_ratio(income: float, expense: float) -> float:
    if income == 0:
        return 1.0
    return min(1.0, expense / income)


def _calculate_credit_score(
    total_tx: int, total_volume: float,
    income_stability: float, savings_consistency: float,
    debt_ratio: float, monthly_income: float
) -> float:

    tx_score = min(25, total_tx * 2)
    vol_score = min(15, total_volume / 100)
    debt_score = max(0, (1 - debt_ratio) * 25)
    inc_score = income_stability * 0.20
    sav_score = savings_consistency * 0.15

    raw_score = tx_score + vol_score + debt_score + inc_score + sav_score
    return min(100, max(0, raw_score))
