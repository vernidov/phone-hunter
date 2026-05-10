from fastapi import APIRouter
from fastapi.responses import FileResponse
import json
import os
from core.database import get_connection

router = APIRouter()

@router.get("/export/{query_id}")
async def export_result(query_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM search_queries WHERE id=?", (query_id,)).fetchone()
    results = conn.execute("SELECT * FROM search_results WHERE query_id=?", (query_id,)).fetchall()
    conn.close()
    
    path = f"report_{query_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"query": dict(row), "results": [dict(r) for r in results]}, f, ensure_ascii=False, indent=2)
    return FileResponse(path, filename=path)
