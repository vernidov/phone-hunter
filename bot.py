import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = "https://phone-hunter-front.onrender.com"
ADMIN_USERNAME = "@vernidov"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    name = user.first_name or "пользователь"
    
    await message.answer(
        f"👋 Приветствую, *{name}*!\n\n"
        f"Добро пожаловать в *Phone Hunter BETA-1.0*\n"
        f"Доступно *5 бесплатных запросов* в день.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🕵️ Открыть Phone Hunter", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💎 Премиум")]
            ],
            resize_keyboard=True
        )
    )
    
    await bot.send_message(
        ADMIN_USERNAME,
        f"🔔 Новый пользователь!\nИмя: {user.full_name}\nUsername: @{user.username or 'нет'}\nID: {user.id}"
    )

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    user = message.from_user
    await message.answer(
        f"👤 *Ваш профиль*\n\nИмя: {user.full_name}\nUsername: @{user.username or 'нет'}\nID: {user.id}",
        parse_mode="Markdown"
    )

@dp.message(F.text == "💎 Премиум")
async def premium(message: types.Message):
    await message.answer("💎 *Phone Hunter Premium*\nБезлимит на 30 дней — 100 Stars.\nПишите @vernidov", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
