from fastapi import APIRouter, HTTPException, Query
from config.database import db
from typing import Optional

router = APIRouter()

@router.get("/hub-list")
def get_hub_list():
	try:
		conn = db.get_mysql_connection()
		cursor = conn.cursor(dictionary=True)
		cursor.execute("SELECT * FROM ms_hub ORDER BY hub_name")
		hubs = cursor.fetchall()
		cursor.close()
		return {"success": True, "data": hubs, "count": len(hubs)}
	except Exception as error:
		raise HTTPException(status_code=500, detail=str(error))

@router.get("/hub-list/location")
def get_hubs_by_location(
    location: str = Query(..., description="Location to filter hubs by"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get hubs filtered by location from MySQL ms_hub table
    """
    try:
        conn = db.get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Count total hubs for the location
        count_query = "SELECT COUNT(*) as total FROM ms_hub WHERE location = %s"
        cursor.execute(count_query, (location,))
        total_count = cursor.fetchone()['total']
        
        # Fetch hubs with pagination
        query = """
            SELECT hub_id, hub_name, location, address 
            FROM ms_hub 
            WHERE location = %s 
            ORDER BY hub_name 
            LIMIT %s
        """
        cursor.execute(query, (location, limit))
        hubs = cursor.fetchall()
        cursor.close()
        
        return {
            "success": True,
            "data": hubs,
            "total_count": total_count,
            "limit": limit,
            "returned_count": len(hubs),
            "filtered_by": {
                "location": location
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching hubs by location: {str(e)}")

@router.get("/hub-list/count")
def get_hub_count():
    """
    Get total count of all hubs for performance
    """
    try:
        conn = db.get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM ms_hub")
        result = cursor.fetchone()
        cursor.close()
        return {"success": True, "total": result['total']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching hub count: {str(e)}")

@router.get("/hub-list/location/count")
def get_hub_count_by_location(
    location: str = Query(..., description="Location to count hubs by")
):
    """
    Get count of hubs filtered by location for performance
    """
    try:
        conn = db.get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM ms_hub WHERE location = %s", (location,))
        result = cursor.fetchone()
        cursor.close()
        return {"success": True, "total": result['total']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching hub count by location: {str(e)}")