import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ["BOT_TOKEN"]  # Токен будет в переменных окружения Render
WEBAPP_URL = "https://phone-hunter-front.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕵️ Открыть Phone Hunter", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("📱 *Phone Hunter BETA-1.0*\nАвтономный OSINT\nНажми кнопку для запуска:", reply_markup=kb, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())