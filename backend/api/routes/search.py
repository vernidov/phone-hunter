from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from modules.aggregator import Aggregator
from typing import Optional
import requests, os

router = APIRouter()
aggregator = Aggregator()
BOT_SERVICE_URL = 'https://phone-hunter-bot.onrender.com'

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")
    
    # Если нет Telegram ID – запрещаем
    if not x_telegram_id:
        raise HTTPException(status_code=400, detail="Missing Telegram ID")
    
    # Проверяем баланс через бота
    try:
        resp = requests.post(
            f'{BOT_SERVICE_URL}/check-balance',
            json={'telegram_id': x_telegram_id},
            timeout=10
        )
        if resp.status_code == 429:
            raise HTTPException(status_code=429, detail="No requests left today")
        elif resp.status_code != 200:
            # Если бот вернул другую ошибку – тоже блокируем (на всякий случай)
            raise HTTPException(status_code=403, detail="Balance check failed")
    except HTTPException:
        raise
    except Exception as e:
        # Если бот не ответил – тоже блокируем
        raise HTTPException(status_code=503, detail=f"Bot unavailable: {e}")
    
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}
