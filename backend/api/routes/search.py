from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from modules.aggregator import Aggregator
from typing import Optional
import requests

router = APIRouter()
aggregator = Aggregator()
BOT_SERVICE_URL = 'https://phone-hunter-bot.onrender.com'

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")
    
    print(f"[CHECK] Получен tg_id: {x_telegram_id}")
    
    if not x_telegram_id:
        print("[CHECK] ID отсутствует, возвращаем 400")
        raise HTTPException(400, "Missing Telegram ID")
    
    try:
        resp = requests.post(
            f'{BOT_SERVICE_URL}/check-balance',
            json={'telegram_id': x_telegram_id},
            timeout=10
        )
        print(f"[CHECK] Бот ответил статусом: {resp.status_code}")
        if resp.status_code == 429:
            print("[CHECK] Возвращаем 429")
            raise HTTPException(429, detail="No requests left today")
        elif resp.status_code != 200:
            print(f"[CHECK] Ошибка бота: {resp.status_code}")
            raise HTTPException(403, detail="Balance check failed")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHECK] Исключение: {e}")
        raise HTTPException(503, detail=f"Bot error: {e}")
    
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}
