"""
Phone Hunter BETA-1.0 — Main entry point
FastAPI application that integrates API routes and OSINT modules.
Полностью локальный режим (без Telegram и облачных зависимостей).
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импортируем роуты из отдельного файла
try:
    from api.routes.search import router as search_router
except ImportError:
    print("[WARNING] Не удалось импортировать api.routes.search. Проверьте структуру папок.")
    search_router = None

PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(
    title="Phone Hunter BETA-1.0",
    version="1.0",
    description="Локальный OSINT-инструмент для поиска информации по номеру телефона",
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
# Разрешаем все запросы для локальной работы с фронтендом (file:// или localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Роуты API ────────────────────────────────────────────────────────────────
if search_router:
    app.include_router(search_router, prefix="/api/v1", tags=["search"])

# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok", "service": "phone-hunter", "version": "1.0", "mode": "local"}

@app.get("/")
async def root():
    return {
        "status": "active", 
        "service": "Phone Hunter BETA-1.0", 
        "mode": "local",
        "docs": "/docs"
    }

# ─── Запуск ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Phone Hunter BETA-1.0 (Local Mode)")
    print(f"  API: http://127.0.0.1:{PORT}")
    print(f"  Docs: http://127.0.0.1:{PORT}/docs")
    print("=" * 50)
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)