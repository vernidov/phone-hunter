from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from modules.aggregator import Aggregator
from core.database import get_user, create_user, increment_requests, reset_daily_requests
from typing import Optional
import sqlite3, os
router = APIRouter()
aggregator = Aggregator()
FREE_LIMIT = 5
class SearchRequest(BaseModel): phone: str
@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone: raise HTTPException(400, "Phone number required")
    if x_telegram_id:
        reset_daily_requests()
        user = get_user(x_telegram_id)
        if not user: create_user(x_telegram_id); user = get_user(x_telegram_id)
        if not user["is_premium"] and user["requests_today"] >= FREE_LIMIT:
            raise HTTPException(status_code=429, detail="Daily limit (5) reached.")
        increment_requests(x_telegram_id)
    result = await aggregator.full_search(phone)
    return {"query_id":"direct","result":result}
