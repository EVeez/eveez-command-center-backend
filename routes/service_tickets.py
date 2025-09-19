from fastapi import APIRouter, HTTPException, Query
from config.database import db
from typing import Optional, List, Any, Dict
import logging
from bson import ObjectId
import json

router = APIRouter()
logger = logging.getLogger(__name__)

def convert_objectid_to_str(obj: Any) -> Any:
    """
    Recursively convert ObjectId and other MongoDB types to JSON-serializable types
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    elif hasattr(obj, '__class__') and obj.__class__.__name__ in ['datetime', 'Decimal', 'BSON']:
        return str(obj)
    else:
        return obj

@router.get("/service-tickets")
def get_service_tickets(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Fetch service tickets from MongoDB service_requests collection
    """
    try:
        mongo_db = db.get_mongo_database()
        collection = mongo_db['service_requests']
        
        # Build query filter - no filters applied
        query_filter = {}
        
        # Get total count
        total_count = collection.count_documents(query_filter)
        
        # Fetch data with pagination
        cursor = collection.find(query_filter).limit(limit)
        service_tickets = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        service_tickets = convert_objectid_to_str(service_tickets)
        
        return {
            "success": True,
            "data": service_tickets,
            "total_count": total_count,
            "limit": limit,
            "returned_count": len(service_tickets)
        }
        
    except Exception as e:
        logger.error(f"Error fetching service tickets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching service tickets: {str(e)}")
