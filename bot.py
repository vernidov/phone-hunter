import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = "https://phone-hunter-front.onrender.com"
ADMIN_USERNAME = "@vernidov"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(commands=["start"])
async def start(message: types.Message):
    user = message.from_user
    name = user.first_name or "пользователь"
    
    # Приветствие
    await message.answer(
        f"👋 Приветствую, *{name}*!\n\n"
        f"Добро пожаловать в *Phone Hunter BETA-1.0* — автономный OSINT-инструмент.\n\n"
        f"Доступно *5 бесплатных запросов* в день.\n\n"
        f"Используй кнопки ниже:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🕵️ Открыть Phone Hunter", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💎 Премиум")]
            ],
            resize_keyboard=True
        )
    )
    
    # Уведомление создателю
    await bot.send_message(
        ADMIN_USERNAME,
        f"🔔 Новый пользователь!\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username or 'нет'}\n"
        f"ID: {user.id}"
    )

@dp.message(lambda msg: msg.text == "👤 Профиль")
async def profile(message: types.Message):
    user = message.from_user
    await message.answer(
        f"👤 *Ваш профиль*\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username or 'нет'}\n"
        f"ID: {user.id}\n\n"
        f"Запросов сегодня: ?/5\n"
        f"Статус: бесплатный",
        parse_mode="Markdown"
    )

@dp.message(lambda msg: msg.text == "💎 Премиум")
async def premium(message: types.Message):
    await message.answer(
        "💎 *Phone Hunter Premium*\n\n"
        "Безлимитные запросы на 30 дней.\n"
        "Цена: 100 Telegram Stars\n\n"
        "Для покупки напишите @vernidov",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
