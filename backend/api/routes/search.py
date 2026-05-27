from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from modules.aggregator import Aggregator

router = APIRouter()
aggregator = Aggregator()

class SearchRequest(BaseModel):
    phone: str

@router.post("/search")
async def search_phone(req: SearchRequest):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(400, "Phone number required")
    
    result = await aggregator.full_search(phone)
    
    return {"query_id": "direct", "result": result}