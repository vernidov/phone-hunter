import os, uvicorn, asyncio, sqlite3, requests
from threading import Thread
from fastapi import FastAPI, APIRouter, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')

BOT_TOKEN = os.environ['BOT_TOKEN']
CRYPTO_API = os.environ.get('CRYPTO_API', '')
WEBAPP_URL = 'https://phone-hunter-front.onrender.com'
ADMIN_ID = 7753936402
PORT = int(os.environ.get('PORT', 8000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, requests_total INTEGER DEFAULT 5, requests_used INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0, last_request_date TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, telegram_id INTEGER, amount REAL, requests INTEGER, currency TEXT, status TEXT)')
    conn.commit()
    conn.close()

def get_user(tg):
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute('SELECT * FROM users WHERE telegram_id=?', (tg,)).fetchone()
    conn.close()
    return r

def create_user(tg, un='', fn=''):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT OR IGNORE INTO users (telegram_id, username, full_name, requests_total, requests_used, last_request_date) VALUES (?,?,?,5,0,date("now"))', (tg, un, fn))
    conn.commit()
    conn.close()

def add_requests(tg, n):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET requests_total=requests_total+? WHERE telegram_id=?', (n, tg))
    conn.commit()
    conn.close()

def use_request(tg):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("UPDATE users SET requests_used = requests_used + 1 WHERE telegram_id=?", (tg,))
    print(f"[use_request] tg={tg}, rows_affected={cur.rowcount}")
    conn.commit()
    conn.close()

def reset_daily(tg):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET requests_used = 0, last_request_date = date('now') WHERE telegram_id=? AND (last_request_date IS NULL OR last_request_date != date('now'))", (tg,))
    conn.commit()
    conn.close()

PRICES = {
    "10": {"requests": 10, "price": 0.99, "name": "10 requests"},
    "50": {"requests": 50, "price": 3.99, "name": "50 requests"},
    "100": {"requests": 100, "price": 6.99, "name": "100 requests"},
    "premium": {"requests": 9999, "price": 9.99, "name": "Unlimited 30 days"}
}

def save_payment(iid, tg, amt, req, cur):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO payments (invoice_id, telegram_id, amount, requests, currency, status) VALUES (?,?,?,?,?,?)', (iid, tg, amt, req, cur, 'pending'))
    conn.commit()
    conn.close()

def mark_paid(iid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE payments SET status=? WHERE invoice_id=?', ('paid', iid))
    conn.commit()
    conn.close()

def get_payment(iid):
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute('SELECT * FROM payments WHERE invoice_id=?', (iid,)).fetchone()
    conn.close()
    return r

def create_invoice(amount, currency='USDT'):
    headers = {'Crypto-Pay-API-Token': CRYPTO_API}
    data = {'asset': currency, 'amount': str(amount)}
    r = requests.post('https://pay.crypt.bot/api/createInvoice', json=data, headers=headers)
    return r.json()

def check_invoice(invoice_id):
    headers = {'Crypto-Pay-API-Token': CRYPTO_API}
    r = requests.get(f'https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}', headers=headers)
    return r.json()

api_app = FastAPI(title="Phone Hunter BETA-1.0", version="1.0")
api_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

search_router = APIRouter()
from modules.aggregator import Aggregator

class SearchRequest(BaseModel):
    phone: str

@search_router.post("/search")
async def search_phone(req: SearchRequest, x_telegram_id: Optional[str] = Header(None)):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")

    if not x_telegram_id:
        raise HTTPException(401, detail="X-Telegram-ID header is required")

    try:
        tg_id = int(x_telegram_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid Telegram ID")

    reset_daily(tg_id)
    user = get_user(tg_id)

    if not user:
        create_user(tg_id, '', '')
        user = get_user(tg_id)

    if not user:
        raise HTTPException(500, detail="Failed to create user")

    remaining = user[3] - user[4]
    if remaining <= 0:
        raise HTTPException(429, detail="No requests left today")

    use_request(tg_id)

    aggregator = Aggregator()
    result = await aggregator.full_search(phone)
    return {"query_id": "direct", "result": result}

api_app.include_router(search_router, prefix="/api/v1", tags=["search"])

@api_app.post("/check-balance")
async def check_balance(data: dict):
    tg_id = data.get("telegram_id")
    if not tg_id:
        raise HTTPException(400, "telegram_id required")
    try:
        tg_id = int(tg_id)
    except ValueError:
        raise HTTPException(400, "Invalid telegram_id")

    reset_daily(tg_id)
    user = get_user(tg_id)
    if not user:
        create_user(tg_id, '', '')
        user = get_user(tg_id)

    if user and user[3] - user[4] > 0:
        use_request(tg_id)
        return {"status": "ok", "remaining": user[3] - user[4] - 1}
    raise HTTPException(429, detail="No requests left today")

@api_app.get("/")
def root():
    return {"status": "active", "service": "Phone Hunter BETA-1.0", "mode": "cloud"}

@dp.message(Command('start'))
async def start(msg: types.Message):
    u = msg.from_user
    create_user(u.id, u.username or '', u.full_name or '')
    await msg.answer(
        f'Hi, *{u.first_name or "user"}*!\n\n*Phone Hunter BETA-1.0*\n5 free requests\nTON / USDT via CryptoBot',
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Open Phone Hunter', web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text='Profile'), KeyboardButton(text='Buy requests')]
        ], resize_keyboard=True))

@dp.message(F.text == 'Profile')
async def profile(msg: types.Message):
    u = msg.from_user
    create_user(u.id, u.username or '', u.full_name or '')
    d = get_user(u.id)
    rem = d[3] - d[4] if d else 5
    status = "Premium" if d and d[5] else "Free"
    await msg.answer(f'*Profile*\n\nName: {u.full_name}\nRequests: *{rem}*\nStatus: {status}', parse_mode='Markdown')

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
    if msg.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute('SELECT * FROM users ORDER BY rowid DESC LIMIT 20').fetchall()
    conn.close()
    txt = '*Admin panel*\n\n'
    for u in users:
        txt += f'ID: {u[0]} | @{u[1] or "none"} | Requests: {u[3]-u[4]}\n'
    await msg.answer(txt, parse_mode='Markdown')

@dp.message(Command('give'))
async def give(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) == 3:
        try:
            tid = int(parts[1])
            amt = int(parts[2])
            add_requests(tid, amt)
            await msg.answer(f'Added {amt} requests to user {tid}')
            await bot.send_message(tid, f'Admin gave you *{amt}* requests!', parse_mode='Markdown')
        except Exception:
            await msg.answer('Format: /give ID amount')
    else:
        await msg.answer('/give ID amount')

async def run_bot():
    init_db()
    await dp.start_polling(bot)

def start_fastapi():
    uvicorn.run(api_app, host="0.0.0.0", port=PORT, reload=False, workers=1)

if __name__ == "__main__":
    Thread(target=start_fastapi, daemon=True).start()
    asyncio.run(run_bot())
