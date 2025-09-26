from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from config.database import db
from dotenv import load_dotenv
from routes.hubs import router as hubs_router
from routes.service_tickets import router as service_tickets_router
from routes.technicians import router as technicians_router
from routes.analytics import router as analytics_router
import os

load_dotenv()

# PERF: Use ORJSON for faster serialization by default in production.
USE_ORJSON = os.getenv("USE_ORJSON", "1") not in ("0", "false", "False")
default_kwargs = {"title": "Eveez Service API", "version": "1.0.0"}
if USE_ORJSON:
    default_kwargs["default_response_class"] = ORJSONResponse

app = FastAPI(**default_kwargs)

# CORS configuration - read allowed origins from env, with secure defaults
DEFAULT_ALLOWED_ORIGINS = [
    "https://eveez.in",
    "https://www.eveez.in",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Add extra origins from environment variable (comma-separated)
extra_origins = os.getenv("ALLOWED_ORIGINS", "")
if extra_origins.strip():
    DEFAULT_ALLOWED_ORIGINS.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hubs_router)
app.include_router(service_tickets_router)
app.include_router(technicians_router, prefix="/api/v1", tags=["technicians"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

@app.get("/")
def root():
    return {"message": "Eveez Service API is running", "status": "healthy"}

@app.get("/city-list")
def get_city_list():
    try:
        conn = db.get_mysql_connection()
        # PERF: use buffered cursor to avoid "Unread result found" and fetchall immediately
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM ms_city ORDER BY city_name")
        cities = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"success": True, "data": cities, "count": len(cities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mongo-test")
def test_mongo():
    try:
        mongo_db = db.get_mongo_database()
        # Test MongoDB connection by listing collections
        collections = mongo_db.list_collection_names()
        return {"success": True, "message": "MongoDB connected successfully", "collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health endpoints (lightweight, no DB by default)
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readiness")
def readiness():
    # Optional DB check via env flag
    check_db = os.getenv("READINESS_CHECK_DB", "0") in ("1", "true", "True")
    if not check_db:
        return {"status": "ready"}
    try:
        conn = db.get_mysql_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchall()
        cur.close()
        conn.close()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"not ready: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
