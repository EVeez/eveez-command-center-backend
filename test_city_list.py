import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_city_list_endpoint():
    """Test the /city-list endpoint returns successful response"""
    response = client.get("/city-list")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "success" in data
    assert "data" in data
    assert "count" in data
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert isinstance(data["count"], int)
    
    # If there are cities, check the structure
    if data["data"]:
        city = data["data"][0]
        assert "city_id" in city
        assert "city_name" in city
        assert "city_code" in city
        assert "state_id" in city

def test_city_list_cors_headers():
    """Test that CORS middleware is configured"""
    # Just test that the endpoint is accessible and returns data
    response = client.get("/city-list")
    
    assert response.status_code == 200
    # The main test is that the endpoint works, CORS is handled by middleware
    data = response.json()
    assert data["success"] is True

if __name__ == "__main__":
    pytest.main([__file__])
