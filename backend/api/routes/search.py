from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from modules.aggregator import Aggregator
from core.database import get_connection
import uuid
from datetime import datetime

router = APIRouter()
aggregator = Aggregator()

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")
    
    query_id = str(uuid.uuid4())
    result = await aggregator.full_search(phone)
    
    conn = get_connection()
    conn.execute(
        "INSERT INTO search_queries (id,phone_number,normalized_phone,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        (query_id, phone, result["query"]["normalized"], "completed", datetime.now().isoformat(), datetime.now().isoformat())
    )
    conn.execute(
        "INSERT INTO search_results (id,query_id,source,raw_data,processed_data,confidence,created_at) VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), query_id, "aggregated", str(result), str(result), 0.9, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    
    return {"query_id": query_id, "result": result}