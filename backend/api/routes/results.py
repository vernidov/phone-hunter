from fastapi import APIRouter, HTTPException
from core.database import get_connection
import json

router = APIRouter()

@router.get("/results/{query_id}")
async def get_result(query_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM search_queries WHERE id=?", (query_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Query not found")
    results = conn.execute("SELECT * FROM search_results WHERE query_id=?", (query_id,)).fetchall()
    conn.close()
    return {"query": dict(row), "results": [dict(r) for r in results]}
