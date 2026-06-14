from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json
import os
from core.database import get_connection

router = APIRouter()

@router.get("/export/{query_id}")
async def export_result(query_id: str):
    try:
        conn = get_connection()
        row = conn.execute("SELECT * FROM search_queries WHERE id=?", (query_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Query not found")
        
        results = conn.execute("SELECT * FROM search_results WHERE query_id=?", (query_id,)).fetchall()
        conn.close()
        
        data = {
            "query": dict(row) if row else {},
            "results": [dict(r) for r in results]
        }
        
        path = f"report_{query_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return FileResponse(path, filename=f"report_{query_id}.json", media_type="application/json")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
