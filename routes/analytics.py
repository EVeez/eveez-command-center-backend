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
    range: Optional[str] = Query(None, description="Time range: today, yesterday, last_7, last_30, or custom"),
    start: Optional[str] = Query(None, description="Start date for custom range (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date for custom range (YYYY-MM-DD)"),
    location: Optional[str] = Query(None, description="Exact location name from service_requests.location"),
    start_date: Optional[str] = Query(None, description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DD)")
):
    """
    Get service requests analytics summary with status counts.
    
    Args:
        range: Time range for filtering (today, yesterday, last_7, last_30, or custom)
        start: Start date for custom range (YYYY-MM-DD format)
        end: End date for custom range (YYYY-MM-DD format)
        location: Optional exact location name from service_requests.location for filtering
        start_date: Start date in ISO format (YYYY-MM-DD) - alternative to range/start/end
        end_date: End date in ISO format (YYYY-MM-DD) - alternative to range/start/end
    """
    try:
        mongo_db = db.get_mongo_database()
        collection = mongo_db['service_requests']
        
        # Handle date range - prioritize start_date/end_date over range parameters
        if start_date and end_date:
            # Use direct date parameters (for frontend integration)
            try:
                ist = get_ist_timezone()
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
                # Convert to IST
                start_date_obj = ist.localize(start_date_obj)
                end_date_obj = ist.localize(end_date_obj)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        elif range:
            # Use existing range logic
            start_date_obj, end_date_obj = get_date_range(range, start, end)
        else:
            raise ValueError("Either range or start_date/end_date must be provided")
        
        # Convert to UTC for MongoDB query (MongoDB stores dates in UTC)
        start_utc = start_date_obj.astimezone(pytz.UTC)
        end_utc = end_date_obj.astimezone(pytz.UTC)
        
        # Build match filter for done requests within date range
        # Using closed_at timestamp for completion (when status becomes done)
        match_filter = {
            "status.done.check": True,
            "date": {
                "$gte": start_utc,
                "$lte": end_utc
            }
        }
        
        # Add location filter if provided (skip if "All Cities" or empty)
        if location and location.strip() and location.strip() != "All Cities":
            loc = location.strip()
            match_filter["location"] = {"$eq": loc}
        
        # Count done requests with filters applied
        done_count = collection.count_documents(match_filter)
        
        # Return minimal response with done count
        return {
            "done_count": done_count
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")
