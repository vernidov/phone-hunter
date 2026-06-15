import os, asyncio, sqlite3, requests, json, traceback
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = os.environ['BOT_TOKEN']
CRYPTO_API = os.environ.get('CRYPTO_API', '')
WEBAPP_URL = 'https://phone-hunter-front.onrender.com'
ADMIN_ID = 7725956756
PORT = int(os.environ.get('PORT', 10000))
DB_PATH = 'users.db'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
CRYPTO_API_URL = 'https://pay.crypt.bot/api'

PRICES = {
    "10": {"requests": 10, "price": 0.99, "name": "10 requests"},
    "50": {"requests": 50, "price": 3.99, "name": "50 requests"},
    "100": {"requests": 100, "price": 6.99, "name": "100 requests"},
    "premium": {"requests": 9999, "price": 9.99, "name": "Unlimited 30 days"},
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, requests_total INTEGER DEFAULT 5, requests_used INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0, last_request_date TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, telegram_id INTEGER, amount REAL, requests INTEGER, currency TEXT, status TEXT)')
    conn.commit(); conn.close()

def get_user(tg): conn=sqlite3.connect(DB_PATH); r=conn.execute('SELECT * FROM users WHERE telegram_id=?',(tg,)).fetchone(); conn.close(); return r
def create_user(tg,un,fn): conn=sqlite3.connect(DB_PATH); conn.execute('INSERT OR IGNORE INTO users (telegram_id,username,full_name,requests_total,requests_used,last_request_date) VALUES (?,?,?,5,0,date("now"))',(tg,un,fn)); conn.commit(); conn.close()
def add_requests(tg,n): conn=sqlite3.connect(DB_PATH); conn.execute('UPDATE users SET requests_total=requests_total+? WHERE telegram_id=?',(n,tg)); conn.commit(); conn.close()
def use_request(tg):
    conn=sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET requests_used = requests_used + 1 WHERE telegram_id=?", (tg,))
    conn.commit(); conn.close()
def reset_daily(tg):
    conn=sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET requests_used = 0, last_request_date = date('now') WHERE telegram_id=? AND (last_request_date IS NULL OR last_request_date != date('now'))", (tg,))
    conn.commit(); conn.close()

# HTTP handler for balance check
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/check-balance':
            try:
                length = int(self.headers.get('Content-Length', 0))
                if length == 0:
                    self.send_response(400); self.end_headers(); self.wfile.write(b'{"error":"Empty body"}'); return
                data = json.loads(self.rfile.read(length))
                tg_id = data.get('telegram_id')
                if not tg_id:
                    self.send_response(400); self.end_headers(); self.wfile.write(b'{"error":"Missing telegram_id"}'); return
                tg_id = int(tg_id)
                reset_daily(tg_id)
                user = get_user(tg_id)
                if not user:
                    create_user(tg_id, '', '')
                    user = get_user(tg_id)
                if user and user[3] - user[4] > 0:
                    use_request(tg_id)
                    self.send_response(200); self.end_headers()
                    self.wfile.write(json.dumps({"status":"ok","remaining":user[3]-user[4]-1}).encode())
                else:
                    self.send_response(429); self.end_headers()
                    self.wfile.write(json.dumps({"status":"error","message":"No requests left"}).encode())
            except Exception as e:
                print(f"Error: {e}"); traceback.print_exc()
                self.send_response(500); self.end_headers()
                self.wfile.write(json.dumps({"error":str(e)}).encode())
        else:
            self.send_response(404); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'bot is running')

def start_web():
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
Thread(target=start_web, daemon=True).start()

# ========== ЕЖЕДНЕВНЫЙ СБРОС ЗАПРОСОВ В 3:00 МСК ==========
async def daily_reset():
    """Обнуляет requests_used для всех пользователей каждый день в 03:00 по московскому времени."""
    while True:
        now = datetime.utcnow() + timedelta(hours=3)  # UTC+3 = MSK
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Сброс
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE users SET requests_used = 0, last_request_date = date('now')")
        conn.commit()
        conn.close()
        print(f"[DAILY RESET] Все запросы обнулены в {datetime.utcnow()+timedelta(hours=3)} MSK")

# ========== КОМАНДЫ БОТА ==========
@dp.message(Command('start'))
async def start(msg: types.Message):
    u = msg.from_user
    create_user(u.id, u.username or '', u.full_name or '')
    # Проверяем, пришёл ли пользователь по ссылке /start buy
    if len(msg.text.split()) > 1 and msg.text.split()[1] == 'buy':
        await shop(msg)  # Открыть меню покупки сразу
        return
    await msg.answer(f'Hi, *{u.first_name or "user"}*!\n\n*Phone Hunter BETA-1.0*\n5 free requests\nTON / USDT via CryptoBot', parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Open Phone Hunter', web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text='Profile'), KeyboardButton(text='Buy requests')]
        ], resize_keyboard=True))

@dp.message(F.text == 'Profile')
async def profile(msg: types.Message):
    u = msg.from_user
    create_user(u.id, u.username or '', u.full_name or '')
    reset_daily(u.id)
    d = get_user(u.id)
    rem = d[3] - d[4] if d else 5
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

@dp.message(Command('give'))
async def give(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("❌ You are not admin")
        return
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("❌ Format: /give TELEGRAM_ID AMOUNT")
        return
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        add_requests(target_id, amount)
        await msg.answer(f"✅ Added {amount} requests to user {target_id}")
        await bot.send_message(target_id, f"🎁 Admin gave you *{amount}* requests!", parse_mode='Markdown')
    except Exception as e:
        await msg.answer(f"❌ Error: {e}")

@dp.message(Command('admin'))
async def admin(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute('SELECT * FROM users ORDER BY rowid DESC LIMIT 20').fetchall()
    conn.close()
    txt = '*Admin panel*\n\n'
    for u in users:
        txt += f'ID: {u[0]} | @{u[1] or "none"} | Requests: {u[3]-u[4]}\n'
    await msg.answer(txt, parse_mode='Markdown')

async def main():
    init_db()
    # Запускаем фоновую задачу ежедневного сброса
    asyncio.create_task(daily_reset())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())