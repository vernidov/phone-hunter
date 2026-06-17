"""
Phone Hunter BETA-1.0 — Main entry point
FastAPI application that integrates API routes and OSINT modules.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импортируем роуты из отдельного файла
from api.routes.search import router as search_router

PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(
    title="Phone Hunter BETA-1.0",
    version="1.0",
    description="OSINT-инструмент для поиска информации по номеру телефона",
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Роуты API ────────────────────────────────────────────────────────────────
app.include_router(search_router, prefix="/api/v1", tags=["search"])


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok", "service": "phone-hunter", "version": "1.0"}


@app.get("/")
async def root():
    return {"status": "active", "service": "Phone Hunter BETA-1.0", "mode": "cloud"}


# ─── Запуск ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
