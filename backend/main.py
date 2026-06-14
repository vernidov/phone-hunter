import os, uvicorn
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from modules.aggregator import Aggregator

PORT = int(os.environ.get('PORT', 8000))

app = FastAPI(title="Phone Hunter BETA-1.0", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

app.include_router(router, prefix="/api/v1", tags=["search"])

@app.get("/")
def root():
    return {"status": "active", "service": "Phone Hunter BETA-1.0", "mode": "cloud"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
