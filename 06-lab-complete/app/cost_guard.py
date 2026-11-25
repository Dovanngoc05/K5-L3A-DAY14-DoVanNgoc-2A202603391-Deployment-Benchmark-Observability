"""
Cost guard (tiêu chí 8).

Yêu cầu:
  • Cộng dồn chi phí LLM (tính theo token) vào Redis
  • Tổng chi phí vượt DAILY_BUDGET_USD (hoặc MONTHLY_BUDGET_USD) → HTTP 402
"""

# Giá USD / 1K tokens (tham khảo gpt-4o-mini)
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006

from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r


def _daily_key() -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"cost:{day}"


def check_budget() -> None:
    spent = float(r.get(_daily_key()) or 0)
    if spent >= settings.daily_budget_usd:
        raise HTTPException(status_code=402, detail="Daily budget exceeded")


def record_cost(input_tokens: int, output_tokens: int) -> float:
    cost = (
        input_tokens * PRICE_INPUT_PER_1K
        + output_tokens * PRICE_OUTPUT_PER_1K
    ) / 1000

    key = _daily_key()
    r.incrbyfloat(key, cost)
    r.expire(key, 172800)
    return cost