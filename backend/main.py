import os, uvicorn, requests
from fastapi import FastAPI, APIRouter, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from modules.aggregator import Aggregator

PORT = int(os.environ.get('PORT', 8000))
BOT_SERVICE_URL = 'https://phone-hunter-bot.onrender.com'

app = FastAPI(title="Phone Hunter BETA-1.0", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

router = APIRouter()
aggregator = Aggregator()

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")
    
    print(f"DEBUG: search request from tg_id: {x_telegram_id}")
    
    if x_telegram_id:
        try:
            resp = requests.post(
                f'{BOT_SERVICE_URL}/check-balance',
                json={'telegram_id': x_telegram_id},
                timeout=10
            )
            print(f"DEBUG: bot response status: {resp.status_code}")
            if resp.status_code == 429:
                raise HTTPException(429, detail="No requests left today")
            elif resp.status_code != 200:
                print(f"DEBUG: bot returned {resp.status_code}")
        except Exception as e:
            print(f"DEBUG: bot check failed: {e}")
    else:
        print("DEBUG: No X-Telegram-ID header")
    
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}

app.include_router(router, prefix="/api/v1", tags=["search"])

@app.get("/")
def root():
    return {"status": "active", "service": "Phone Hunter BETA-1.0", "mode": "cloud"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
