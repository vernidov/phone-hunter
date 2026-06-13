# -*- coding: utf-8 -*-
import os, asyncio, sqlite3, requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = os.environ['BOT_TOKEN']
CRYPTO_API = os.environ['CRYPTO_API']
WEBAPP_URL = 'https://phone-hunter-front.onrender.com'
ADMIN_ID = 7753936402
DB_PATH = 'users.db'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
CRYPTO_API_URL = 'https://pay.crypt.bot/api'

PRICES = {
    "10": {"requests": 10, "price": 0.99, "name": "10 запросов"},
    "50": {"requests": 50, "price": 3.99, "name": "50 запросов"},
    "100": {"requests": 100, "price": 6.99, "name": "100 запросов"},
    "premium": {"requests": 9999, "price": 9.99, "name": "Безлимит 30 дней"},
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, requests_total INTEGER DEFAULT 5, requests_used INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, telegram_id INTEGER, amount REAL, requests INTEGER, currency TEXT, status TEXT)')
    conn.commit(); conn.close()

def get_user(tg): conn=sqlite3.connect(DB_PATH); r=conn.execute('SELECT * FROM users WHERE telegram_id=?',(tg,)).fetchone(); conn.close(); return r
def create_user(tg,un,fn): conn=sqlite3.connect(DB_PATH); conn.execute('INSERT OR IGNORE INTO users (telegram_id,username,full_name) VALUES (?,?,?)',(tg,un,fn)); conn.commit(); conn.close()
def add_requests(tg,n): conn=sqlite3.connect(DB_PATH); conn.execute('UPDATE users SET requests_total=requests_total+? WHERE telegram_id=?',(n,tg)); conn.commit(); conn.close()
def save_payment(iid,tg,amt,req,cur): conn=sqlite3.connect(DB_PATH); conn.execute('INSERT INTO payments (invoice_id,telegram_id,amount,requests,currency,status) VALUES (?,?,?,?,?,?)',(iid,tg,amt,req,cur,'pending')); conn.commit(); conn.close()
def mark_paid(iid): conn=sqlite3.connect(DB_PATH); conn.execute('UPDATE payments SET status=? WHERE invoice_id=?',('paid',iid)); conn.commit(); conn.close()
def get_payment(iid): conn=sqlite3.connect(DB_PATH); r=conn.execute('SELECT * FROM payments WHERE invoice_id=?',(iid,)).fetchone(); conn.close(); return r

def create_invoice(amount, currency='USDT'):
    headers = {'Crypto-Pay-API-Token': CRYPTO_API}
    data = {'asset': currency, 'amount': str(amount)}
    r = requests.post(f'{CRYPTO_API_URL}/createInvoice', json=data, headers=headers)
    return r.json()

def check_invoice(invoice_id):
    headers = {'Crypto-Pay-API-Token': CRYPTO_API}
    r = requests.get(f'{CRYPTO_API_URL}/getInvoices?invoice_ids={invoice_id}', headers=headers)
    return r.json()

@dp.message(Command('start'))
async def start(msg: types.Message):
    u = msg.from_user; create_user(u.id, u.username or '', u.full_name or '')
    await msg.answer(
        f'?? Привет, *{u.first_name or "пользователь"}*!\n\n*Phone Hunter BETA-1.0*\n?? 5 бесплатных запросов\n?? Оплата TON / USDT через CryptoBot\nАвто-начисление после оплаты!',
        parse_mode='Markdown',
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
            [InlineKeyboardButton(text='?? 10 запросов — TON', callback_data='buy_10_TON')],
            [InlineKeyboardButton(text='?? 50 запросов — TON', callback_data='buy_50_TON')],
            [InlineKeyboardButton(text='?? 100 запросов — TON', callback_data='buy_100_TON')],
            [InlineKeyboardButton(text='?? Безлимит 30д — TON', callback_data='buy_premium_TON')],
            [InlineKeyboardButton(text='---------------', callback_data='none')],
            [InlineKeyboardButton(text='?? 10 запросов — USDT', callback_data='buy_10_USDT')],
            [InlineKeyboardButton(text='?? 50 запросов — USDT', callback_data='buy_50_USDT')],
            [InlineKeyboardButton(text='?? 100 запросов — USDT', callback_data='buy_100_USDT')],
            [InlineKeyboardButton(text='?? Безлимит 30д — USDT', callback_data='buy_premium_USDT')],
        ]))

@dp.callback_query(F.data.startswith('buy_'))
async def buy(call: types.CallbackQuery):
    parts = call.data.replace('buy_','').split('_')
    pkg = parts[0]; currency = parts[1]; pd = PRICES[pkg]
    invoice = create_invoice(pd['price'], currency)
    if invoice.get('ok'):
        result = invoice['result']; iid = result['invoice_id']; pay_url = result['bot_invoice_url']
        save_payment(iid, call.from_user.id, pd['price'], pd['requests'], currency)
        await call.message.answer(
            f'?? *Счёт создан!*\n\nПакет: {pd["name"]}\nСумма: {pd["price"]} {currency}\n\nНажмите кнопку для оплаты:',
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f'?? Оплатить {pd["price"]} {currency}', url=pay_url)],
                [InlineKeyboardButton(text='?? Проверить оплату', callback_data=f'check_{iid}_{pkg}')]
            ]))
    else: await call.message.answer('? Ошибка создания счёта.')
    await call.answer()

@dp.callback_query(F.data.startswith('check_'))
async def check(call: types.CallbackQuery):
    parts = call.data.replace('check_','').split('_')
    iid = int(parts[0]); pkg = parts[1]; pd = PRICES[pkg]
    result = check_invoice(iid)
    if result.get('ok') and result['result']['items']:
        inv = result['result']['items'][0]
        if inv['status'] == 'paid':
            payment = get_payment(iid)
            if payment and payment[6] != 'paid':
                add_requests(payment[2], pd['requests']); mark_paid(iid)
                await call.message.answer(f'? Оплата получена! +{pd["requests"]} запросов!')
                await bot.send_message(payment[2], f'? Оплата прошла! Начислено *{pd["requests"]}* запросов!', parse_mode='Markdown')
            else: await call.message.answer('? Этот счёт уже оплачен.')
        else: await call.message.answer('? Оплата ещё не поступила.')
    else: await call.message.answer('? Счёт не найден.')
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
