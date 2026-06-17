"""
backend/api/routes/search.py
Phone Hunter — роут поиска (исправленная версия).

Исправления:
  1. Использует реальный OSINT-агрегатор вместо заглушки
  2. Правильный URL бота: https://phone-hunter-bot.onrender.com/check-balance
  3. При ответе 429 от бота — возвращаем HTTP 429
  4. Эндпоинт /balance для проверки баланса без списания
  5. Эндпоинт /health для проверки доступности сервиса
  6. Подробное логирование для отладки
  7. Маппинг данных модулей в единый формат ответа API
"""

import logging
import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

# ─── Импортируем реальный агрегатор ────────────────────────────────────────────
from modules.aggregator import Aggregator

# ─── Настройка логгера ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phone_hunter.search")

# ─── Константы ────────────────────────────────────────────────────────────────
BOT_URL = "https://phone-hunter-bot.onrender.com"
BOT_CHECK_BALANCE_ENDPOINT = f"{BOT_URL}/check-balance"
BOT_TIMEOUT_SECONDS = 15  # Render cold-start может занять до 30с

router = APIRouter()
aggregator = Aggregator()


# ─── Health check ──────────────────────────────────────────────────────────────
@router.get("/health")
@router.head("/health")
async def health():
    return {"status": "ok"}


# ─── Вызов бота для проверки и списания баланса ───────────────────────────────
async def _call_bot_check_balance(telegram_id: str) -> dict:
    """
    Вызывает бота для проверки и списания одного запроса.
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
            remaining = data.get("remaining", 0)
            return {"ok": True, "balance": int(remaining), "status": 200}

        if response.status_code == 429:
            return {"ok": False, "balance": 0, "status": 429}

        if response.status_code == 404:
            logger.warning("User not found in bot | telegram_id=%s", telegram_id)
            return {"ok": False, "balance": 0, "status": 404}

        logger.error("Unexpected bot response | status=%d | body=%s", response.status_code, response.text[:500])
        return {"ok": False, "balance": 0, "status": response.status_code}

    except httpx.TimeoutException:
        logger.error("Bot timeout | telegram_id=%s | timeout=%ds", telegram_id, BOT_TIMEOUT_SECONDS)
        raise HTTPException(status_code=503, detail="Bot service timeout. Try again in a few seconds.")

    except httpx.ConnectError as exc:
        logger.error("Bot connection error | telegram_id=%s | err=%s", telegram_id, exc)
        raise HTTPException(status_code=503, detail="Bot service unavailable. Try again later.")


# ─── Маппинг данных агрегатора в формат API ──────────────────────────────────

def _map_hlr_data(hlr: dict) -> dict:
    """Приводит HLR-данные к единому формату."""
    return {
        "operator": hlr.get("provider", hlr.get("operator", "N/A")),
        "country": hlr.get("country", "N/A"),
        "region": hlr.get("region", "N/A"),
        "city": hlr.get("city", "N/A"),
        "line_type": hlr.get("network_type", "unknown"),
        "ported": bool(hlr.get("ported", False)),
        "roaming": bool(hlr.get("roaming", False)),
        "mcc": hlr.get("mcc", ""),
        "mnc": hlr.get("mnc", ""),
        "valid": bool(hlr.get("provider") or hlr.get("country")),
    }


def _map_messenger_data(msg: dict) -> dict:
    """Приводит данные мессенджеров к формату с registered/username."""
    mapped = {}
    for app in ["telegram", "whatsapp", "viber", "signal", "wechat"]:
        registered = bool(msg.get(app, False))
        mapped[app] = {
            "registered": registered,
            "username": None,
        }
    return mapped


def _map_leak_data(leak: dict) -> dict:
    """Приводит данные утечек к единому формату."""
    return {
        "found": bool(leak.get("found_in_leaks", False)),
        "count": len(leak.get("leaks", [])),
        "sources": leak.get("leaks", []),
        "emails": leak.get("emails", []),
        "passwords": leak.get("passwords", []),
    }


def _map_fraud_data(fraud: dict) -> dict:
    """Приводит данные о мошенничестве к единому формату."""
    complaints = int(fraud.get("complaint_count", 0))
    has_complaints = bool(fraud.get("has_complaints", False)) or complaints > 0
    # Определяем уровень риска
    if complaints > 5:
        risk = "high"
    elif complaints > 0 or has_complaints:
        risk = "medium"
    else:
        risk = "low"
    return {
        "complaints": complaints,
        "has_complaints": has_complaints,
        "risk_level": risk,
        "tags": fraud.get("tags", []),
        "names": fraud.get("names", []),
        "sources": fraud.get("sources", []),
    }


def _map_social_data(social: dict) -> dict:
    """Приводит данные соцсетей."""
    return {
        "vk": social.get("vk"),
        "ok": social.get("ok"),
        "instagram": social.get("instagram"),
        "facebook": social.get("facebook"),
        "telegram": social.get("telegram"),
        "whatsapp": social.get("whatsapp"),
        "other_mentions": social.get("other_mentions", []),
    }


# ─── Эндпоинт поиска ──────────────────────────────────────────────────────────

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
      200 — результат поиска с remaining_credits
      400 — не передан номер или заголовок
      429 — нет запросов (баланс = 0)
      503 — бот недоступен
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
                    "remaining_credits": 0,
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

        raise HTTPException(status_code=502, detail="Bot returned unexpected response")

    remaining = bot_result["balance"]
    logger.info("Credits deducted | telegram_id=%s | remaining=%d", x_telegram_id, remaining)

    # 4. Выполняем реальный OSINT-поиск через Aggregator
    try:
        raw = await aggregator.full_search(phone)
    except Exception as e:
        logger.error("OSINT search error | phone=%s | err=%s", phone, e)
        raise HTTPException(status_code=500, detail="Search failed: internal error")

    # 5. Маппинг данных в формат для фронтенда
    hlr_data = _map_hlr_data(raw.get("hlr", {}))
    messenger_data = _map_messenger_data(raw.get("messengers", {}))
    leak_data = _map_leak_data(raw.get("leaks", {}))
    fraud_data = _map_fraud_data(raw.get("fraud", {}))
    social_data = _map_social_data(raw.get("social", {}))

    # 6. Возвращаем результат с остатком баланса
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "phone": phone,
            "remaining_credits": remaining,
            "hlr": hlr_data,
            "messengers": messenger_data,
            "leaks": leak_data,
            "fraud": fraud_data,
            "social": social_data,
            "risk_score": raw.get("risk_score", 0),
            "query": raw.get("query", {}),
        },
    )


# ─── Проверка баланса (без списания) ──────────────────────────────────────────

@router.get("/balance")
async def get_balance(
    x_telegram_id: str | None = Header(default=None, alias="X-Telegram-ID"),
):
    """
    GET /api/v1/balance

    Возвращает текущий баланс пользователя без списания.
    Используется фронтендом при загрузке страницы.

    Ответ: {"ok": bool, "balance": int}
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
            bal = int(data.get("remaining", data.get("balance", 0)))
            return {"ok": True, "balance": bal}

        if response.status_code == 404:
            logger.warning("User not found in bot | telegram_id=%s", x_telegram_id)
            return {"ok": True, "balance": 0}

        logger.error("Bot error | status=%d | body=%s", response.status_code, response.text[:200])
        raise HTTPException(status_code=502, detail="Bot error")

    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="Bot timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Bot unavailable")
