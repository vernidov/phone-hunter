# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from modules.aggregator import Aggregator
from typing import Optional
import requests, os

router = APIRouter()
aggregator = Aggregator()
BOT_SERVICE_URL = 'https://phone-hunter-crypto-bot.onrender.com'

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")
    
    if x_telegram_id:
        try:
            resp = requests.post(
                f'{BOT_SERVICE_URL}/check-balance',
                json={'telegram_id': x_telegram_id},
                timeout=10
            )
            if resp.status_code == 429:
                raise HTTPException(429, detail="No requests left today")
        except HTTPException:
            raise
        except:
            pass
    
    result = await aggregator.full_search(phone)
    return {"query_id":"direct","result":result}
