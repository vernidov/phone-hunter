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
    
    # ===== СПИСЫВАЕМ ЗАПРОС ЧЕРЕЗ БОТА =====
    if x_telegram_id:
        try:
            resp = requests.post(
                f'{BOT_SERVICE_URL}/check-balance',
                json={'telegram_id': x_telegram_id},
                timeout=10
            )
            if resp.status_code == 429:
                raise HTTPException(429, detail="No requests left today")
            elif resp.status_code != 200:
                print(f"[!] Бот вернул {resp.status_code}, тело: {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Ошибка при вызове бота: {e}")
            # Если бот не ответил — пропускаем проверку (но лучше вернуть ошибку)
            # raise HTTPException(503, detail="Bot unavailable")
    else:
        print("[!] Запрос без X-Telegram-ID — пропускаем списание")
    
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}
