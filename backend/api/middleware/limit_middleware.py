from fastapi import Request, HTTPException
from core.database import get_user, create_user, increment_requests, reset_daily_requests

FREE_LIMIT = 5

async def check_limit(request: Request, telegram_id: str):
    reset_daily_requests()
    user = get_user(telegram_id)
    if not user:
        create_user(telegram_id)
        user = get_user(telegram_id)
    if user and not user.get("is_premium") and user.get("requests_today", 0) >= FREE_LIMIT:
        raise HTTPException(status_code=429, detail="Daily limit reached.")
    if user:
        increment_requests(telegram_id)
