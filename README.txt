OSINT Phone Hunter Pro v2.0
================================
ПОЛНОСТЬЮ АВТОНОМНАЯ СИСТЕМА

Не требует:
- API ключей
- Регистраций
- Платных подписок
- Tor прокси

Всё работает локально, ищет по открытым источникам напрямую.

ЗАПУСК:
1. Установите Python 3.10+
2. Запустите run.bat
3. Откройте http://127.0.0.1:8000/docs

ИЛИ вручную:
cd backend
pip install -r requirements.txt
python main.py

API Эндпоинты:
POST /api/v1/search  {"phone": "+79001234567"}
GET  /api/v1/results/{query_id}
GET  /api/v1/export/{query_id}

Интерфейс: http://127.0.0.1:8000/docs (Swagger)
