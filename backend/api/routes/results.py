from fastapi import APIRouter, HTTPException
from core.database import get_connection
import json

router = APIRouter()

@router.get("/results/{query_id}")
async def get_result(query_id: str):
    try:
        conn = get_connection()
        row = conn.execute("SELECT * FROM search_queries WHERE id=?", (query_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Query not found")
        results = conn.execute("SELECT * FROM search_results WHERE query_id=?", (query_id,)).fetchall()
        conn.close()
        return {"query": dict(row) if row else {}, "results": [dict(r) for r in results]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
