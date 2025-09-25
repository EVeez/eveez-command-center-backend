from fastapi import APIRouter, HTTPException, Query
from config.database import db
from typing import Optional, List, Any, Dict
import logging
from bson import ObjectId
import json
from utils.city_aliases import normalize_city_for_technician_count

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

@router.get("/technicians")
def get_technicians(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Fetch technicians from MongoDB users collection with role: "Technician" only
    """
    try:
        mongo_db = db.get_mongo_database()
        collection = mongo_db['users']
        
        # Build query filter - ALWAYS filter for role: "Technician"
        query_filter = {"role": "Technician"}
        
        # Get total count
        total_count = collection.count_documents(query_filter)
        
        # Fetch data with pagination
        # PERF: project only needed fields to reduce payload/CPU
        cursor = collection.find(query_filter, projection={"_id": 1, "name": 1, "location": 1, "role": 1}).limit(limit)
        technicians = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        technicians = convert_objectid_to_str(technicians)
        
        return {
            "success": True,
            "data": technicians,
            "total_count": total_count,
            "limit": limit,
            "returned_count": len(technicians),
            "filtered_by_role": "Technician"
        }
        
    except Exception as e:
        logger.error(f"Error fetching technicians: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching technicians: {str(e)}")

@router.get("/technicians/location")
def get_technicians_by_location(
    city: Optional[str] = Query(None, description="City to filter technicians by (optional)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get technician counts by city from MongoDB users collection.
    Returns aggregated data with city counts and total.
    """
    try:
        mongo_db = db.get_mongo_database()
        collection = mongo_db['users']
        
        # Build base query filter for role: "Technician"
        base_filter = {"role": "Technician"}
        
        if city:
            # Narrow-scoped normalization ONLY for Total Technicians metric
            raw_city = city
            norm_city = normalize_city_for_technician_count(raw_city)
            # One-time debug when alias triggers (prod log level remains unchanged)
            if raw_city and raw_city.strip() != norm_city:
                logger.debug(f"[TECH-ALIAS] TotalTechnicians: '{raw_city}' -> '{norm_city}'")

            # If UI passes All/All Cities, bypass city filter entirely
            if norm_city and norm_city.strip().casefold() in ("all", "all cities"):
                query_filter = {**base_filter}
            else:
                # If specific city requested, return count for that city only
                query_filter = {
                    **base_filter,
                    # Case-insensitive city search with normalized value
                    "location": {"$regex": norm_city, "$options": "i"}
                }
            
            count = collection.count_documents(query_filter)
            
            return {
                "success": True,
                # Return the normalized city label that was used for filtering
                "data": [{"city": norm_city if norm_city else city, "count": count}],
                "total": count,
                "filtered_by": {"city": norm_city if norm_city else city}
            }
        else:
            # Aggregate technicians by city
            pipeline = [
                {"$match": base_filter},
                {
                    "$group": {
                        "_id": "$location",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$project": {
                        "city": "$_id",
                        "count": 1,
                        "_id": 0
                    }
                },
                {"$sort": {"city": 1}}
            ]
            
            # Execute aggregation
            result = list(collection.aggregate(pipeline))
            
            # Calculate total count across all cities
            total_count = sum(item["count"] for item in result)
            
            return {
                "success": True,
                "data": result,
                "total": total_count,
                "cities_count": len(result)
            }
        
    except Exception as e:
        logger.error(f"Error fetching technicians by location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching technicians by location: {str(e)}")
