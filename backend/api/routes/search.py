# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from modules.aggregator import Aggregator
from typing import Optional
import sqlite3, os, requests

router = APIRouter()
aggregator = Aggregator()
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_ID = '7753936402'
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "users.db")

def get_user(tg):
    try:
        if not os.path.exists(DB_PATH): return None
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute('SELECT * FROM users WHERE telegram_id=?', (tg,)).fetchone()
        conn.close(); return r
    except: return None

def use_request(tg):
    try:
        if not os.path.exists(DB_PATH): return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE users SET requests_used = requests_used + 1 WHERE telegram_id=?", (tg,))
        conn.commit(); conn.close()
    except: pass

def reset_daily(tg):
    try:
        if not os.path.exists(DB_PATH): return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE users SET requests_used = 0, last_request_date = date('now') WHERE telegram_id=? AND last_request_date != date('now')", (tg,))
        conn.commit(); conn.close()
    except: pass

def create_user(tg, un='', fn=''):
    try:
        if not os.path.exists(DB_PATH): return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR IGNORE INTO users (telegram_id, username, full_name, requests_total, requests_used, last_request_date) VALUES (?,?,?,5,0,date('now'))", (tg, un, fn))
        conn.commit(); conn.close()
    except: pass

def notify_admin(phone, tg_id, username):
    try:
        if not BOT_TOKEN: return
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', json={
            'chat_id': ADMIN_ID,
            'text': f'New search!\nPhone: {phone}\nUser: @{username or "none"}\nID: {tg_id}'
        })
    except: pass

class SearchRequest(BaseModel): phone: str

@router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None), x_telegram_username: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone: raise HTTPException(400, "Phone number required")
    try:
        if x_telegram_id:
            reset_daily(x_telegram_id)
            user = get_user(x_telegram_id)
            if not user: create_user(x_telegram_id, x_telegram_username or ''); user = get_user(x_telegram_id)
            if user and user[3] - user[4] <= 0: raise HTTPException(429, detail="No requests left today")
            use_request(x_telegram_id)
            notify_admin(phone, x_telegram_id, x_telegram_username or '')
    except HTTPException: raise
    except: pass
    result = await aggregator.full_search(phone)
    return {"query_id":"direct","result":result}
