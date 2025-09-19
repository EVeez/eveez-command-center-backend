from fastapi import APIRouter, HTTPException, Query
from config.database import db
from typing import Optional
from datetime import datetime, timedelta
import pytz
from bson import ObjectId

router = APIRouter()

def get_ist_timezone():
    """Get IST timezone object"""
    return pytz.timezone('Asia/Kolkata')

def get_date_range(range_type: str, start: Optional[str] = None, end: Optional[str] = None):
    """
    Get start and end datetime for different range types in IST timezone
    """
    ist = get_ist_timezone()
    now = datetime.now(ist)
    
    if range_type == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    elif range_type == "yesterday":
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    elif range_type == "last_7":
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    elif range_type == "last_30":
        start_date = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    elif range_type == "custom":
        if not start or not end:
            raise ValueError("start and end dates are required for custom range")
        
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            # Convert to IST
            start_date = ist.localize(start_date)
            end_date = ist.localize(end_date)
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    else:
        raise ValueError(f"Invalid range type: {range_type}")
    
    return start_date, end_date

@router.get("/analytics/service-requests/summary")
def get_service_requests_summary(
    range: str = Query(..., description="Time range: today, yesterday, last_7, last_30, or custom"),
    start: Optional[str] = Query(None, description="Start date for custom range (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date for custom range (YYYY-MM-DD)")
):
    """
    Get service requests analytics summary with status counts
    """
    try:
        mongo_db = db.get_mongo_database()
        collection = mongo_db['service_requests']
        
        # Get date range
        start_date, end_date = get_date_range(range, start, end)
        
        # Convert to UTC for MongoDB query (MongoDB stores dates in UTC)
        start_utc = start_date.astimezone(pytz.UTC)
        end_utc = end_date.astimezone(pytz.UTC)
        
        # 1. Get total count of done requests (unfiltered by date)
        done_total_unfiltered = collection.count_documents({
            "status.done.check": True
        })
        
        # 2. Get filtered counts for the date range
        # Build aggregation pipeline for status counts
        pipeline = [
            {
                "$match": {
                    "date": {
                        "$gte": start_utc,
                        "$lte": end_utc
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "to_do": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status.to_do.check", True]}, 1, 0]
                        }
                    },
                    "in_progress": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status.in_progress.check", True]}, 1, 0]
                        }
                    },
                    "done": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status.done.check", True]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        result = list(collection.aggregate(pipeline))
        
        if result:
            filtered_counts = {
                "to_do": result[0]["to_do"],
                "in_progress": result[0]["in_progress"],
                "done": result[0]["done"]
            }
        else:
            filtered_counts = {
                "to_do": 0,
                "in_progress": 0,
                "done": 0
            }
        
        # Format response
        response = {
            "done_total_unfiltered": done_total_unfiltered,
            "filtered_counts": filtered_counts,
            "meta": {
                "range": range,
                "start_iso": start_date.isoformat(),
                "end_iso": end_date.isoformat()
            }
        }
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")
