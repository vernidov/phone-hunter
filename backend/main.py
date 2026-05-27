import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Phone Hunter BETA-1.0", version="1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

try:
    from api.routes.search import router as search_router
    app.include_router(search_router, prefix="/api/v1", tags=["search"])
except ImportError:
    pass

try:
    from api.routes.results import router as results_router
    app.include_router(results_router, prefix="/api/v1", tags=["results"])
except ImportError:
    pass

try:
    from api.routes.export import router as export_router
    app.include_router(export_router, prefix="/api/v1", tags=["export"])
except ImportError:
    pass

@app.get("/")
def root():
    return {"status": "active", "service": "Phone Hunter BETA-1.0", "mode": "autonomous"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
