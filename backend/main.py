import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import search, results, export

app = FastAPI(title="OSINT Phone Hunter", version="2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(results.router, prefix="/api/v1", tags=["results"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])

@app.get("/")
def root():
    return {"status": "active", "service": "OSINT Phone Hunter Pro", "mode": "fully autonomous"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
