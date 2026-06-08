from fastapi import Request, HTTPException
from core.database import get_user, create_user, increment_requests

FREE_LIMIT = 5

async def check_limit(request: Request, telegram_id: str):
    from core.database import reset_daily_requests
    reset_daily_requests()
    user = get_user(telegram_id)
    if not user:
        create_user(telegram_id)
        user = get_user(telegram_id)
    if not user["is_premium"] and user["requests_today"] >= FREE_LIMIT:
        raise HTTPException(status_code=429, detail="Daily limit reached.")
    increment_requests(telegram_id)
