import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Phone Hunter BETA-1.0", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

try:
    from api.routes.search import router as s
    app.include_router(s, prefix="/api/v1", tags=["search"])
except Exception as e:
    print(f"Error loading search router: {e}")

@app.get("/")
def root(): return {"status":"active","service":"Phone Hunter BETA-1.0","mode":"cloud"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
