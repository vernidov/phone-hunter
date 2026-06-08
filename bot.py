import os, asyncio, sqlite3, uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from yookassa import Configuration, Payment

BOT_TOKEN = os.environ['BOT_TOKEN']
WEBAPP_URL = 'https://phone-hunter-front.onrender.com'
ADMIN_ID = 7753936402
DB_PATH = 'users.db'
Configuration.account_id = os.environ.get('YOOKASSA_SHOP_ID','')
Configuration.secret_key = os.environ.get('YOOKASSA_SECRET_KEY','')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, requests_total INTEGER DEFAULT 5, requests_used INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS payments (id TEXT PRIMARY KEY, telegram_id INTEGER, amount REAL, requests INTEGER, status TEXT)')
    conn.commit(); conn.close()

def get_user(tg): conn=sqlite3.connect(DB_PATH); r=conn.execute('SELECT * FROM users WHERE telegram_id=?',(tg,)).fetchone(); conn.close(); return r
def create_user(tg,un,fn): conn=sqlite3.connect(DB_PATH); conn.execute('INSERT OR IGNORE INTO users (telegram_id,username,full_name) VALUES (?,?,?)',(tg,un,fn)); conn.commit(); conn.close()
def add_requests(tg,n): conn=sqlite3.connect(DB_PATH); conn.execute('UPDATE users SET requests_total=requests_total+? WHERE telegram_id=?',(n,tg)); conn.commit(); conn.close()
def save_payment(pid,tg,amt,req): conn=sqlite3.connect(DB_PATH); conn.execute('INSERT INTO payments (id,telegram_id,amount,requests,status) VALUES (?,?,?,?,?)',(pid,tg,amt,req,'paid')); conn.commit(); conn.close()

PRICES = {'10':{'price':99.0,'requests':10,'name':'10 запросов'},'50':{'price':399.0,'requests':50,'name':'50 запросов'},'100':{'price':699.0,'requests':100,'name':'100 запросов'},'premium':{'price':999.0,'requests':9999,'name':'Безлимит 30 дней'}}

@dp.message(Command('start'))
async def start(msg: types.Message):
    u = msg.from_user; create_user(u.id, u.username or '', u.full_name or '')
    await msg.answer(f'?? Привет, *{u.first_name or "юзер"}*!\n\nPhone Hunter BETA-1.0\n?? 5 бесплатных запросов\n?? Оплата картой/СБП', parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='??? Открыть Phone Hunter', web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text='?? Профиль'), KeyboardButton(text='?? Купить запросы')]
        ], resize_keyboard=True))

@dp.message(F.text == '?? Профиль')
async def profile(msg: types.Message):
    u = msg.from_user; create_user(u.id, u.username or '', u.full_name or '')
    d = get_user(u.id); rem = d[3]-d[4] if d else 5
    await msg.answer(f'?? *Профиль*\n\nИмя: {u.full_name}\nЗапросов: *{rem}*\nСтатус: {"?? Премиум" if d and d[5] else "?? Бесплатный"}', parse_mode='Markdown')

@dp.message(F.text == '?? Купить запросы')
async def shop(msg: types.Message):
    await msg.answer('?? *Выберите пакет:*', parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='?? 10 запросов — 99?', callback_data='pay_10')],
            [InlineKeyboardButton(text='?? 50 запросов — 399?', callback_data='pay_50')],
            [InlineKeyboardButton(text='?? 100 запросов — 699?', callback_data='pay_100')],
            [InlineKeyboardButton(text='?? Безлимит 30д — 999?', callback_data='pay_premium')]
        ]))

@dp.callback_query(F.data.startswith('pay_'))
async def pay(call: types.CallbackQuery):
    pkg = call.data.replace('pay_',''); pd = PRICES[pkg]
    payment = Payment.create({
        'amount': {'value': str(pd['price']), 'currency': 'RUB'},
        'confirmation': {'type': 'redirect', 'return_url': 'https://t.me/phone_hunter_vernidov_bot'},
        'description': f'Phone Hunter - {pd["name"]}',
        'metadata': {'telegram_id': call.from_user.id, 'requests': pd['requests']}
    }, uuid.uuid4())
    await call.message.answer(f'?? Счёт на {pd["price"]}?\nПакет: {pd["name"]}\n\nНажмите кнопку для оплаты:', parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='?? Оплатить', url=payment.confirmation.confirmation_url)]
        ]))
    await call.answer()

@dp.message(Command('admin'))
async def admin(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    conn = sqlite3.connect(DB_PATH); users = conn.execute('SELECT * FROM users ORDER BY rowid DESC LIMIT 20').fetchall(); conn.close()
    txt = '?? *Админ-панель*\n\n'
    for u in users: txt += f'ID: {u[0]} | @{u[1] or "нет"} | Запросов: {u[3]-u[4]}\n'
    await msg.answer(txt, parse_mode='Markdown')

@dp.message(Command('give'))
async def give(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split()
    if len(parts)==3:
        try:
            tid=int(parts[1]); amt=int(parts[2]); add_requests(tid,amt)
            await msg.answer(f'? Выдано {amt} запросов пользователю {tid}')
            await bot.send_message(tid, f'?? Админ выдал *{amt}* запросов!', parse_mode='Markdown')
        except: await msg.answer('? Формат: /give ID количество')
    else: await msg.answer('? /give ID количество')

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
