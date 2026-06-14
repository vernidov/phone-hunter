import os, uvicorn, asyncio, sqlite3, requests
from threading import Thread
from fastapi import FastAPI, APIRouter, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = os.environ['BOT_TOKEN']
CRYPTO_API = os.environ.get('CRYPTO_API','')
WEBAPP_URL = 'https://phone-hunter-front.onrender.com'
ADMIN_ID = 7753936402
PORT = int(os.environ.get('PORT', 8000))
DB_PATH = 'users.db'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, requests_total INTEGER DEFAULT 5, requests_used INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0, last_request_date TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, telegram_id INTEGER, amount REAL, requests INTEGER, currency TEXT, status TEXT)')
    conn.commit(); conn.close()

def get_user(tg): conn=sqlite3.connect(DB_PATH); r=conn.execute('SELECT * FROM users WHERE telegram_id=?',(tg,)).fetchone(); conn.close(); return r
def create_user(tg,un,fn): conn=sqlite3.connect(DB_PATH); conn.execute('INSERT OR IGNORE INTO users (telegram_id,username,full_name,requests_total,requests_used,last_request_date) VALUES (?,?,?,5,0,date("now"))',(tg,un,fn)); conn.commit(); conn.close()
def add_requests(tg,n): conn=sqlite3.connect(DB_PATH); conn.execute('UPDATE users SET requests_total=requests_total+? WHERE telegram_id=?',(n,tg)); conn.commit(); conn.close()
def use_request(tg): conn=sqlite3.connect(DB_PATH); conn.execute("UPDATE users SET requests_used = requests_used + 1 WHERE telegram_id=?", (tg,)); conn.commit(); conn.close()
def reset_daily(tg): conn=sqlite3.connect(DB_PATH); conn.execute("UPDATE users SET requests_used = 0, last_request_date = date('now') WHERE telegram_id=? AND last_request_date != date('now')", (tg,)); conn.commit(); conn.close()

PRICES = {"10":{"requests":10,"price":0.99,"name":"10 requests"},"50":{"requests":50,"price":3.99,"name":"50 requests"},"100":{"requests":100,"price":6.99,"name":"100 requests"},"premium":{"requests":9999,"price":9.99,"name":"Unlimited 30 days"}}

api_app = FastAPI(title="Phone Hunter BETA-1.0", version="1.0")
api_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

search_router = APIRouter()
from modules.aggregator import Aggregator

class SearchRequest(BaseModel): phone: str

@search_router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone: raise HTTPException(400, "Phone number required")
    if x_telegram_id:
        reset_daily(x_telegram_id)
        user = get_user(x_telegram_id)
        if not user: create_user(x_telegram_id); user = get_user(x_telegram_id)
        if user and user[3] - user[4] <= 0: raise HTTPException(429, detail="No requests left today")
        use_request(x_telegram_id)
    aggregator = Aggregator()
    result = await aggregator.full_search(phone)
    return {"query_id":"direct","result":result}

api_app.include_router(search_router, prefix="/api/v1", tags=["search"])

@api_app.get("/")
def root(): return {"status":"active","service":"Phone Hunter BETA-1.0","mode":"cloud"}

@dp.message(Command('start'))
async def start(msg: types.Message):
    u = msg.from_user; create_user(u.id, u.username or '', u.full_name or '')
    await msg.answer(f'Hi, *{u.first_name or "user"}*!\n\n*Phone Hunter BETA-1.0*\n5 free requests\nTON / USDT via CryptoBot', parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Open Phone Hunter', web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text='Profile'), KeyboardButton(text='Buy requests')]
        ], resize_keyboard=True))

@dp.message(F.text == 'Profile')
async def profile(msg: types.Message):
    u = msg.from_user; create_user(u.id, u.username or '', u.full_name or '')
    d = get_user(u.id); rem = d[3]-d[4] if d else 5
    await msg.answer(f'*Profile*\n\nName: {u.full_name}\nRequests: *{rem}*\nStatus: {"Premium" if d and d[5] else "Free"}', parse_mode='Markdown')

@dp.message(F.text == 'Buy requests')
async def shop(msg: types.Message):
    await msg.answer('*Choose package:*', parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='10 requests - TON', callback_data='buy_10_TON')],
            [InlineKeyboardButton(text='50 requests - TON', callback_data='buy_50_TON')],
            [InlineKeyboardButton(text='100 requests - TON', callback_data='buy_100_TON')],
            [InlineKeyboardButton(text='Unlimited 30d - TON', callback_data='buy_premium_TON')],
            [InlineKeyboardButton(text='---------------', callback_data='none')],
            [InlineKeyboardButton(text='10 requests - USDT', callback_data='buy_10_USDT')],
            [InlineKeyboardButton(text='50 requests - USDT', callback_data='buy_50_USDT')],
            [InlineKeyboardButton(text='100 requests - USDT', callback_data='buy_100_USDT')],
            [InlineKeyboardButton(text='Unlimited 30d - USDT', callback_data='buy_premium_USDT')],
        ]))

@dp.message(Command('admin'))
async def admin(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    conn = sqlite3.connect(DB_PATH); users = conn.execute('SELECT * FROM users ORDER BY rowid DESC LIMIT 20').fetchall(); conn.close()
    txt = '*Admin panel*\n\n'
    for u in users: txt += f'ID: {u[0]} | @{u[1] or "none"} | Requests: {u[3]-u[4]}\n'
    await msg.answer(txt, parse_mode='Markdown')

@dp.message(Command('give'))
async def give(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split()
    if len(parts)==3:
        try:
            tid=int(parts[1]); amt=int(parts[2]); add_requests(tid,amt)
            await msg.answer(f'Added {amt} requests to user {tid}')
            await bot.send_message(tid, f'Admin gave you *{amt}* requests!', parse_mode='Markdown')
        except: await msg.answer('Format: /give ID amount')
    else: await msg.answer('/give ID amount')

async def run_bot():
    init_db()
    await dp.start_polling(bot)

def start_fastapi():
    uvicorn.run(api_app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    Thread(target=start_fastapi, daemon=True).start()
    asyncio.run(run_bot())
