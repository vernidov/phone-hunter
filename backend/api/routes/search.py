from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from modules.aggregator import Aggregator
from typing import Optional
import sqlite3, os

router = APIRouter()
aggregator = Aggregator()
FREE_LIMIT = 5
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "users.db")

def get_user(tg):
    try:
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute('SELECT * FROM users WHERE telegram_id=?', (tg,)).fetchone()
        conn.close()
        return r
    except:
        return None

def use_request(tg):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('UPDATE users SET requests_used = requests_used + 1 WHERE telegram_id=?', (tg,))
        conn.commit()
        conn.close()
    except:
        pass

def create_user(tg, un='', fn=''):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR IGNORE INTO users (telegram_id, username, full_name, last_request_date) VALUES (?,?,?,date(\"now\"))', (tg, un, fn))
        conn.commit()
        conn.close()
    except:
        pass

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")
    
    try:
        if x_telegram_id:
            user = get_user(x_telegram_id)
            if not user:
                create_user(x_telegram_id)
                user = get_user(x_telegram_id)
            
            if user:
                remaining = user[3] - user[4]
                if remaining <= 0:
                    raise HTTPException(429, detail="No requests left. Buy more via bot.")
                use_request(x_telegram_id)
    except HTTPException:
        raise
    except:
        pass
    
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}
