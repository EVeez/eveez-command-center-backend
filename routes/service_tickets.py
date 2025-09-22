from fastapi import APIRouter, HTTPException, Query
from config.database import db
from typing import Optional, List, Any, Dict, Tuple
import logging
from bson import ObjectId
import json
from datetime import datetime, timedelta, timezone


router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed request types for aggregation endpoint
ALLOWED_TYPES: List[str] = [
    "Running Repair At Hub",
    "Breakdown Support",
    "Monthly Service",
    "Under Repair At Hub",
    "Refurbishment Service Request",
]

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


def parse_request_types(param: Optional[str]) -> List[str]:
    """Parse comma-separated request_type param and filter to allowed list."""
    if not param:
        return ALLOWED_TYPES.copy()
    provided = [p.strip() for p in param.split(",") if p.strip()]
    filtered = [p for p in provided if p in ALLOWED_TYPES]
    return filtered if filtered else ALLOWED_TYPES.copy()


def resolve_date_range(
    range_param: Optional[str],
    start: Optional[str],
    end: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Resolve date range to UTC start and exclusive end datetimes.

    Returns (start_dt, end_dt) where end_dt is exclusive (i.e., < end_dt).
    """
    def parse_ymd(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if start_date and end_date:
        s = parse_ymd(start_date)
        e = parse_ymd(end_date) + timedelta(days=1)
        return s, e

    if range_param == "custom":
        if not start or not end:
            raise HTTPException(status_code=400, detail="start and end are required when range=custom (YYYY-MM-DD)")
        s = parse_ymd(start)
        e = parse_ymd(end) + timedelta(days=1)
        return s, e

    today_utc = datetime.now(timezone.utc).date()
    if range_param == "today":
        s = datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc)
        e = s + timedelta(days=1)
        return s, e
    if range_param == "yesterday":
        e = datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc)
        s = e - timedelta(days=1)
        return s, e
    if range_param == "last_7":
        e = datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
        s = e - timedelta(days=7)
        return s, e
    if range_param == "last_30":
        e = datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
        s = e - timedelta(days=30)
        return s, e

    # No date filtering requested
    return None, None


def choose_date_field(collection) -> Optional[str]:
    """Choose primary date field by sampling a document.

    Preference order: created_at, createdAt, date, date_time, assigned_to.date_time, updated_at.
    """
    candidate_fields = [
        "created_at",
        "createdAt",
        "date",
        "date_time",
        "assigned_to.date_time",
        "updated_at",
    ]
    try:
        sample = collection.find_one({}, projection={
            "created_at": 1,
            "createdAt": 1,
            "date": 1,
            "date_time": 1,
            "assigned_to.date_time": 1,
            "updated_at": 1,
        }) or {}
        # Check presence in order
        for field in candidate_fields:
            parts = field.split(".")
            value = sample
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
            if value is not None:
                return field
        return None
    except Exception:
        return None


@router.get("/service-tickets/request-type")
def get_request_type_counts(
    request_type: Optional[str] = Query(None, description="Comma-separated list of allowed request types"),
    location: Optional[str] = Query(None, description="Exact match on service_requests.location"),
    range: Optional[str] = Query(None, description="One of today,yesterday,last_7,last_30,custom"),
    start: Optional[str] = Query(None, description="YYYY-MM-DD (required if range=custom)"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD (required if range=custom)"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD alternative to range/start/end"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD alternative to range/start/end"),
):
    """Return counts of service_requests grouped by request_type for the allowed set.

    Note: Consider adding an index for performance: { request_type: 1, location: 1, created_at: 1 }
    or replace created_at with the detected date field.
    """
    try:
        mongo_db = db.get_mongo_database()
        collection = mongo_db["service_requests"]

        # Determine requested/allowed types
        requested_types = parse_request_types(request_type)

        # Resolve date range
        start_dt, end_dt = resolve_date_range(range, start, end, start_date, end_date)

        # Build $match
        match: Dict[str, Any] = {"request_type": {"$in": requested_types}}
        if location:
            match["location"] = location

        date_field_used: Optional[str] = None
        if start_dt or end_dt:
            date_field_used = choose_date_field(collection)
            if not date_field_used:
                raise HTTPException(status_code=400, detail="Date filtering requested but no recognized date field found in service_requests")

            # Build date filter path (support nested)
            if date_field_used == "assigned_to.date_time":
                # If value is an object like { $date: ... }, Mongo will still compare correctly when stored as Date. If stored as object, this may not work; best-effort.
                date_path = "assigned_to.date_time"
            else:
                date_path = date_field_used

            date_filter: Dict[str, Any] = {}
            if start_dt:
                date_filter["$gte"] = start_dt
            if end_dt:
                date_filter["$lt"] = end_dt
            match[date_path] = date_filter

        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$request_type", "count": {"$sum": 1}}},
        ]

        agg_results = list(collection.aggregate(pipeline))

        counts_map: Dict[str, int] = {doc.get("_id", ""): int(doc.get("count", 0)) for doc in agg_results}

        # Fill zeros for missing requested types
        data = [{"request_type": rt, "count": counts_map.get(rt, 0)} for rt in requested_types]
        total = sum(item["count"] for item in data)

        # Prepare filters info
        start_str = start_dt.date().isoformat() if start_dt else None
        # end_dt is exclusive; return end_date - 1 day to represent inclusive range
        end_inclusive = (end_dt - timedelta(days=1)).date().isoformat() if end_dt else None

        return {
            "data": data,
            "filters": {
                "location": location if location else None,
                "date_field_used": date_field_used,
                "start_date": start_str,
                "end_date": end_inclusive,
            },
            "total": total,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aggregating request types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch request type counts")
