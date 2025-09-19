from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config.database import db
from dotenv import load_dotenv
from routes.hubs import router as hubs_router
from routes.service_tickets import router as service_tickets_router
from routes.technicians import router as technicians_router

load_dotenv()
app = FastAPI(title="Eveez Service API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hubs_router)
app.include_router(service_tickets_router)
app.include_router(technicians_router, prefix="/api/v1", tags=["technicians"])

@app.get("/")
def root():
    return {"message": "Eveez Service API is running", "status": "healthy"}

@app.get("/city-list")
def get_city_list():
    try:
        conn = db.get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ms_city ORDER BY city_name")
        cities = cursor.fetchall()
        cursor.close()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
