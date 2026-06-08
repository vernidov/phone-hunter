import os, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
def get_user(tg):
    conn=sqlite3.connect(DB_PATH); r=conn.execute("SELECT * FROM users WHERE telegram_id=?",(tg,)).fetchone(); conn.close(); return r
def create_user(tg,un=""):
    conn=sqlite3.connect(DB_PATH); conn.execute("INSERT OR IGNORE INTO users (telegram_id,username,last_request_date) VALUES (?,?,date('now'))",(tg,un)); conn.commit(); conn.close()

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = "https://phone-hunter-front.onrender.com"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="??? Открыть Phone Hunter", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("?? *Phone Hunter BETA-1.0*\nАвтономный OSINT по номеру телефона\nНажми кнопку чтобы открыть:", reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("profile"))
async def profile(message: types.Message):
    tg = str(message.from_user.id)
    user = get_user(tg)
    if not user: create_user(tg, message.from_user.username or ""); user = get_user(tg)
    remaining = 5 - user["requests_today"]
    status = "?? Premium" if user["is_premium"] else "?? Free"
    await message.answer(f"?? *Профиль*\nID: {user['telegram_id']}\nСтатус: {status}\nЗапросов сегодня: {user['requests_today']}/5\nОсталось: {remaining}\nДата регистрации: {user['created_at']}", parse_mode="Markdown")

@dp.message(Command("balance"))
async def balance(message: types.Message):
    await message.answer("?? Пополнение баланса через Telegram Stars пока в разработке.")

@dp.message(Command("buy"))
async def buy(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="?? Premium (30 дней) — 100 ?", callback_data="buy_premium")]
    ])
    await message.answer("Выберите тариф:", reply_markup=kb)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer("?? *Команды:*\n/profile — профиль и лимиты\n/balance — пополнить баланс\n/buy — купить Premium\n/start — открыть Phone Hunter", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
