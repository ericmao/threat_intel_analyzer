from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import init, check_postgres_connection, check_es_connection
from routes import api_keys, analysis

app = FastAPI(title="Threat Intelligence Analyzer")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(api_keys.router, prefix="/api", tags=["API Keys & Models"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])

@app.on_event("startup")
async def startup_event():
    """Initialize databases on startup."""
    try:
        init()
    except Exception as e:
        print(f"Error during initialization: {e}")
        raise

@app.get("/api/health")
async def health_check():
    """Check the health of all services."""
    postgres_ok = check_postgres_connection()
    es_ok = check_es_connection()
    
    status = {
        "postgres": "healthy" if postgres_ok else "unhealthy",
        "elasticsearch": "healthy" if es_ok else "unhealthy"
    }
    
    if not (postgres_ok and es_ok):
        raise HTTPException(
            status_code=503,
            detail="One or more services are unhealthy",
            headers={"x-status": str(status)}
        )
    
    return {
        "status": "healthy",
        "services": status
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
