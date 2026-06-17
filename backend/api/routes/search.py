"""
backend/api/routes/search.py
Phone Hunter — исправленный роут поиска.

Исправления:
  1. Правильный URL бота: https://phone-hunter-bot.onrender.com/check-balance
  2. При ответе 429 от бота — возвращаем HTTP 429
  3. Добавлено подробное логирование для отладки
  4. Обработка таймаута и недоступности бота
"""

import logging
import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

# ─── Настройка логгера ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phone_hunter.search")

# ─── Константы ───────────────────────────────────────────────────────────────
BOT_URL = "https://phone-hunter-bot.onrender.com"
BOT_CHECK_BALANCE_ENDPOINT = f"{BOT_URL}/check-balance"
BOT_DEDUCT_ENDPOINT        = f"{BOT_URL}/deduct"       # если используешь отдельный endpoint
BOT_TIMEOUT_SECONDS = 15   # Render cold-start может занять до 30с, но 15 достаточно

router = APIRouter()


async def _call_bot_check_balance(telegram_id: str) -> dict:
    """
    Вызывает бота для проверки и списания одного запроса.

    Ожидаемые коды ответа от бота:
      200  — запрос списан, в теле {"balance": N, "ok": true}
      429  — нет запросов, в теле {"detail": "No credits"}
      404  — пользователь не найден в боте

    Возвращает: dict с ключами {"ok": bool, "balance": int, "status": int}
    """
    payload = {"telegram_id": str(telegram_id)}
    logger.info("Calling bot check-balance | telegram_id=%s | url=%s", telegram_id, BOT_CHECK_BALANCE_ENDPOINT)

    try:
        async with httpx.AsyncClient(timeout=BOT_TIMEOUT_SECONDS) as client:
            response = await client.post(BOT_CHECK_BALANCE_ENDPOINT, json=payload)

        logger.info(
            "Bot response | telegram_id=%s | status=%d | body=%s",
            telegram_id,
            response.status_code,
            response.text[:200],
        )

        if response.status_code == 200:
            data = response.json()
            return {"ok": True, "balance": data.get("balance", 0), "status": 200}

        if response.status_code == 429:
            return {"ok": False, "balance": 0, "status": 429}

        if response.status_code == 404:
            logger.warning("User not found in bot | telegram_id=%s", telegram_id)
            return {"ok": False, "balance": 0, "status": 404}

        # Любой другой код — логируем и считаем ошибкой
        logger.error("Unexpected bot response | status=%d | body=%s", response.status_code, response.text[:500])
        return {"ok": False, "balance": 0, "status": response.status_code}

    except httpx.TimeoutException:
        logger.error("Bot timeout | telegram_id=%s | timeout=%ds", telegram_id, BOT_TIMEOUT_SECONDS)
        raise HTTPException(status_code=503, detail="Bot service timeout. Try again in a few seconds.")

    except httpx.ConnectError as exc:
        logger.error("Bot connection error | telegram_id=%s | err=%s", telegram_id, exc)
        raise HTTPException(status_code=503, detail="Bot service unavailable. Try again later.")


# ─── Эндпоинт поиска ─────────────────────────────────────────────────────────

@router.post("/search")
async def search_phone(
    request: Request,
    x_telegram_id: str | None = Header(default=None, alias="X-Telegram-ID"),
):
    """
    POST /api/v1/search

    Заголовок запроса:
      X-Telegram-ID: <числовой Telegram ID пользователя>

    Тело запроса (JSON):
      { "phone": "+79991234567" }

    Возможные ответы:
      200  — результат поиска
      400  — не передан номер или заголовок
      429  — нет запросов (баланс = 0)
      503  — бот недоступен
    """

    # 1. Валидация Telegram ID
    if not x_telegram_id:
        logger.warning("Missing X-Telegram-ID header")
        raise HTTPException(status_code=400, detail="Missing X-Telegram-ID header")

    if not x_telegram_id.isdigit():
        logger.warning("Invalid X-Telegram-ID: %s", x_telegram_id)
        raise HTTPException(status_code=400, detail="X-Telegram-ID must be a numeric string")

    # 2. Получаем тело запроса
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    phone = body.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Field 'phone' is required")

    logger.info("Search request | telegram_id=%s | phone=%s", x_telegram_id, phone)

    # 3. Проверяем и списываем баланс через бота
    bot_result = await _call_bot_check_balance(x_telegram_id)

    if not bot_result["ok"]:
        status = bot_result["status"]

        if status == 429:
            logger.info("No credits | telegram_id=%s", x_telegram_id)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "No credits left. Please buy more requests in the bot.",
                    "code": "NO_CREDITS",
                },
            )

        if status == 404:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "User not found. Please start the bot first: @PhoneHunterBot",
                    "code": "USER_NOT_FOUND",
                },
            )

        # Прочие ошибки бота
        raise HTTPException(status_code=502, detail="Bot returned unexpected response")

    remaining = bot_result["balance"]
    logger.info("Credits deducted | telegram_id=%s | remaining=%d", x_telegram_id, remaining)

    # 4. Выполняем реальный OSINT-поиск
    result = await _perform_osint_lookup(phone)

    # 5. Возвращаем результат с остатком баланса
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "phone": phone,
            "remaining_credits": remaining,
            "data": result,
        },
    )


@router.get("/balance")
async def get_balance(
    x_telegram_id: str | None = Header(default=None, alias="X-Telegram-ID"),
):
    """
    GET /api/v1/balance

    Возвращает текущий баланс пользователя без списания.
    Используется фронтендом при загрузке страницы.
    """
    if not x_telegram_id or not x_telegram_id.isdigit():
        raise HTTPException(status_code=400, detail="Missing or invalid X-Telegram-ID header")

    logger.info("Balance check | telegram_id=%s", x_telegram_id)

    try:
        async with httpx.AsyncClient(timeout=BOT_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{BOT_URL}/balance",
                params={"telegram_id": x_telegram_id},
            )

        if response.status_code == 200:
            data = response.json()
            return {"ok": True, "balance": data.get("balance", 0)}

        if response.status_code == 404:
            return {"ok": False, "balance": 0, "detail": "User not found in bot"}

        raise HTTPException(status_code=502, detail="Bot error")

    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="Bot timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Bot unavailable")


# ─── Заглушка OSINT-логики ────────────────────────────────────────────────────
# Замени эту функцию своей реальной реализацией (нумерация API, HLR и т.д.)

async def _perform_osint_lookup(phone: str) -> dict:
    """
    Заглушка для реальной OSINT-логики.
    Замени содержимое своей реализацией, например вызовами:
      - numverify / abstract-api для оператора и страны
      - HaveIBeenPwned для утечек
      - CheckWho / WhoCallsMe для жалоб на мошенничество
    """
    import re

    # Минимальная нормализация номера
    digits = re.sub(r"\D", "", phone)

    # Пример возвращаемой структуры (замени реальными запросами)
    return {
        "phone": phone,
        "normalized": f"+{digits}",
        "carrier": {
            "name": "Unknown",
            "country": "Unknown",
            "line_type": "unknown",
            "mnp": False,
        },
        "messengers": {
            "telegram": None,
            "whatsapp": None,
            "viber": None,
            "signal": None,
        },
        "leaks": [],
        "fraud_reports": 0,
        "source": "stub — replace with real OSINT calls",
    }