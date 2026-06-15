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
        raise HTTPException(status_code=400, detail="Phone number required")
    
    print(f"[DEBUG] Получен tg_id: {x_telegram_id}")
    
    if x_telegram_id:
        try:
            resp = requests.post(
                f'{BOT_SERVICE_URL}/check-balance',
                json={'telegram_id': x_telegram_id},
                timeout=10
            )
            print(f"[DEBUG] Бот ответил статусом: {resp.status_code}")
            if resp.status_code == 429:
                print("[DEBUG] Возвращаем 429 клиенту")
                raise HTTPException(status_code=429, detail="No requests left today")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[DEBUG] Ошибка при вызове бота: {e}")
    else:
        print("[DEBUG] tg_id не передан, блокируем запрос")
        raise HTTPException(status_code=400, detail="Missing Telegram ID")
    
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}
