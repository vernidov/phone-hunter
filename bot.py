# -*- coding: utf-8 -*-
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

PRICES = {'10':{'price':99.0,'requests':10,'name':'10 requests'},'50':{'price':399.0,'requests':50,'name':'50 requests'},'100':{'price':699.0,'requests':100,'name':'100 requests'},'premium':{'price':999.0,'requests':9999,'name':'Unlimited 30 days'}}

@dp.message(Command('start'))
async def start(msg: types.Message):
    u = msg.from_user; create_user(u.id, u.username or '', u.full_name or '')
    await msg.answer(f'Hi, *{u.first_name or "user"}*!\n\nPhone Hunter BETA-1.0\n5 free requests\nPay by card', parse_mode='Markdown',
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
            [InlineKeyboardButton(text='10 requests - 99 RUB', callback_data='pay_10')],
            [InlineKeyboardButton(text='50 requests - 399 RUB', callback_data='pay_50')],
            [InlineKeyboardButton(text='100 requests - 699 RUB', callback_data='pay_100')],
            [InlineKeyboardButton(text='Unlimited 30d - 999 RUB', callback_data='pay_premium')]
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
    await call.message.answer(f'Bill: {pd["price"]} RUB\nPackage: {pd["name"]}\n\nPress to pay:', parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Pay', url=payment.confirmation.confirmation_url)]
        ]))
    await call.answer()

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

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
