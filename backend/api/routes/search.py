"""
backend/api/routes/search.py
Phone Hunter — роут поиска (ЛОКАЛЬНАЯ ВЕРСИЯ).
Без Telegram, без бота, без лимитов.
Просто OSINT-поиск по номеру телефона.
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

# Импортируем реальный агрегатор
from modules.aggregator import Aggregator

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phone_hunter.search")

router = APIRouter()
aggregator = Aggregator()

# Health check
@router.get("/health")
@router.head("/health")
async def health():
    return {"status": "ok", "mode": "local"}

# Эндпоинт поиска (без Telegram и лимитов)
@router.post("/search")
async def search_phone(request: Request):
    """
    POST /api/v1/search
    Тело запроса (JSON):
        {"phone": "+79991234567"}
    Возвращает результат OSINT-поиска.
    """
    # 1. Получаем тело запроса
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    phone = body.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Field 'phone' is required")
    
    logger.info("Search request | phone=%s", phone)
    
    # 2. Выполняем OSINT-поиск через Aggregator
    try:
        raw = await aggregator.full_search(phone)
    except Exception as e:
        logger.error("OSINT search error | phone=%s | err=%s", phone, e)
        raise HTTPException(status_code=500, detail="Search failed: internal error")
    
    # 3. Маппинг данных в формат, который ожидает фронтенд
    # Фронтенд ожидает структуру:
    # result.query.normalized
    # result.hlr.city, region, provider
    # result.validation.country, operator
    # result.risk_score
    # result.messengers (объект)
    # result.leaks.found_in_leaks, leaks
    # result.fraud.has_complaints, tags
    # result.line_type.is_business, is_mass_activation
    # result.port.ported
    
    hlr_data = raw.get("hlr", {})
    messenger_data = raw.get("messengers", {})
    leak_data = raw.get("leaks", {})
    fraud_data = raw.get("fraud", {})
    social_data = raw.get("social", {})
    
    # Формируем ответ в формате фронтенда
    result = {
        "query": {
            "normalized": raw.get("query", {}).get("normalized", phone),
        },
        "hlr": {
            "city": hlr_data.get("city", ""),
            "region": hlr_data.get("region", ""),
            "area": hlr_data.get("area", ""),
            "provider": hlr_data.get("provider", hlr_data.get("operator", "")),
            "country": hlr_data.get("country", ""),
            "ported": bool(hlr_data.get("ported", False)),
        },
        "validation": {
            "country": hlr_data.get("country", ""),
            "operator": hlr_data.get("provider", hlr_data.get("operator", "")),
        },
        "geo": {
            "city": hlr_data.get("city", ""),
            "region_name": hlr_data.get("region", ""),
        },
        "risk_score": raw.get("risk_score", 0),
        "messengers": {
            "Telegram": bool(messenger_data.get("telegram", False)),
            "WhatsApp": bool(messenger_data.get("whatsapp", False)),
            "Viber": bool(messenger_data.get("viber", False)),
            "Signal": bool(messenger_data.get("signal", False)),
        },
        "leaks": {
            "found_in_leaks": bool(leak_data.get("found", leak_data.get("found_in_leaks", False))),
            "leaks": leak_data.get("sources", leak_data.get("leaks", [])),
        },
        "fraud": {
            "has_complaints": bool(fraud_data.get("has_complaints", False)),
            "tags": fraud_data.get("tags", []),
            "complaint_count": fraud_data.get("complaints", 0),
        },
        "line_type": {
            "is_business": hlr_data.get("line_type", "").lower() == "business",
            "is_mass_activation": hlr_data.get("line_type", "").lower() == "mass",
        },
        "port": {
            "ported": bool(hlr_data.get("ported", False)),
        },
        "social": social_data,
    }
    
    logger.info("Search completed | phone=%s", phone)
    
    return JSONResponse(
        status_code=200,
        content={"result": result},
    )