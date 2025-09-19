import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database for testing"""
    with patch('config.database.db.get_mongo_database') as mock_db:
        mock_collection = MagicMock()
        mock_db.return_value = {'users': mock_collection}
        yield mock_collection

def test_get_technicians_by_location_all_cities(mock_mongo_db):
    """Test getting technician counts for all cities"""
    # Mock aggregation result
    mock_aggregation_result = [
        {"city": "Delhi", "count": 15},
        {"city": "Mumbai", "count": 12},
        {"city": "Bangalore", "count": 8}
    ]
    
    mock_mongo_db.aggregate.return_value = mock_aggregation_result
    
    response = client.get("/api/v1/technicians/location")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) == 3
    assert data["total"] == 35  # 15 + 12 + 8
    assert data["cities_count"] == 3
    
    # Verify aggregation pipeline was called correctly
    mock_mongo_db.aggregate.assert_called_once()
    call_args = mock_mongo_db.aggregate.call_args[0][0]
    assert call_args[0]["$match"] == {"role": "Technician"}

def test_get_technicians_by_location_specific_city(mock_mongo_db):
    """Test getting technician count for a specific city"""
    mock_mongo_db.count_documents.return_value = 15
    
    response = client.get("/api/v1/technicians/location?city=Delhi")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["city"] == "Delhi"
    assert data["data"][0]["count"] == 15
    assert data["total"] == 15
    assert data["filtered_by"]["city"] == "Delhi"
    
    # Verify count_documents was called with correct filter
    mock_mongo_db.count_documents.assert_called_once()
    call_args = mock_mongo_db.count_documents.call_args[0][0]
    assert call_args["role"] == "Technician"
    assert "location" in call_args

def test_get_technicians_by_location_no_technicians(mock_mongo_db):
    """Test when no technicians are found"""
    mock_mongo_db.aggregate.return_value = []
    
    response = client.get("/api/v1/technicians/location")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"] == []
    assert data["total"] == 0
    assert data["cities_count"] == 0

def test_get_technicians_by_location_database_error(mock_mongo_db):
    """Test handling of database errors"""
    mock_mongo_db.aggregate.side_effect = Exception("Database connection error")
    
    response = client.get("/api/v1/technicians/location")
    
    assert response.status_code == 500
    data = response.json()
    assert "Error fetching technicians by location" in data["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
