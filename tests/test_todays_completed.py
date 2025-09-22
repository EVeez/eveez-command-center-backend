import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.database import db

client = TestClient(app)

class TestTodaysCompletedAnalytics:
    """Test suite for today's completed service requests analytics endpoint"""
    
    def setup_method(self):
        """Setup test data for each test method"""
        self.ist = pytz.timezone('Asia/Kolkata')
        self.today = datetime.now(self.ist).date()
        self.today_start = self.ist.localize(datetime.combine(self.today, datetime.min.time()))
        self.today_end = self.ist.localize(datetime.combine(self.today, datetime.max.time()))
        
        # Convert to UTC for MongoDB queries
        self.today_start_utc = self.today_start.astimezone(pytz.UTC)
        self.today_end_utc = self.today_end.astimezone(pytz.UTC)
    
    @patch('config.database.db.get_mongo_database')
    def test_get_todays_completed_all_cities(self, mock_get_mongo_db):
        """Test getting today's completed count for all cities"""
        # Mock MongoDB collection
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 25
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_db.return_value = mock_db
        
        # Make API request
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": self.today.strftime("%Y-%m-%d"),
            "end_date": self.today.strftime("%Y-%m-%d")
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["done_count"] == 25
        
        # Verify MongoDB query
        expected_filter = {
            "status.done.check": True,
            "date": {
                "$gte": self.today_start_utc,
                "$lte": self.today_end_utc
            }
        }
        mock_collection.count_documents.assert_called_once_with(expected_filter)
    
    @patch('config.database.db.get_mongo_database')
    def test_get_todays_completed_specific_city(self, mock_get_mongo_db):
        """Test getting today's completed count for a specific city"""
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 8
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_db.return_value = mock_db
        
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": self.today.strftime("%Y-%m-%d"),
            "end_date": self.today.strftime("%Y-%m-%d"),
            "location": "Kolkata"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["done_count"] == 8
        
        # Verify MongoDB query includes location filter
        expected_filter = {
            "status.done.check": True,
            "date": {
                "$gte": self.today_start_utc,
                "$lte": self.today_end_utc
            },
            "location": {"$eq": "Kolkata"}
        }
        mock_collection.count_documents.assert_called_once_with(expected_filter)
    
    @patch('config.database.db.get_mongo_database')
    def test_get_todays_completed_all_cities_explicit(self, mock_get_mongo_db):
        """Test that 'All Cities' location parameter is ignored"""
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 30
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_db.return_value = mock_db
        
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": self.today.strftime("%Y-%m-%d"),
            "end_date": self.today.strftime("%Y-%m-%d"),
            "location": "All Cities"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["done_count"] == 30
        
        # Verify MongoDB query does NOT include location filter
        expected_filter = {
            "status.done.check": True,
            "date": {
                "$gte": self.today_start_utc,
                "$lte": self.today_end_utc
            }
        }
        mock_collection.count_documents.assert_called_once_with(expected_filter)
    
    @patch('config.database.db.get_mongo_database')
    def test_get_todays_completed_empty_location(self, mock_get_mongo_db):
        """Test that empty location parameter is ignored"""
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 12
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_db.return_value = mock_db
        
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": self.today.strftime("%Y-%m-%d"),
            "end_date": self.today.strftime("%Y-%m-%d"),
            "location": ""
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["done_count"] == 12
        
        # Verify MongoDB query does NOT include location filter
        expected_filter = {
            "status.done.check": True,
            "date": {
                "$gte": self.today_start_utc,
                "$lte": self.today_end_utc
            }
        }
        mock_collection.count_documents.assert_called_once_with(expected_filter)
    
    def test_invalid_date_format(self):
        """Test that invalid date format returns 400 error"""
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": "invalid-date",
            "end_date": self.today.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]
    
    def test_missing_date_parameters(self):
        """Test that missing date parameters returns 400 error"""
        response = client.get("/api/v1/analytics/service-requests/summary")
        
        assert response.status_code == 400
        assert "Either range or start_date/end_date must be provided" in response.json()["detail"]
    
    @patch('config.database.db.get_mongo_database')
    def test_mongodb_error_handling(self, mock_get_mongo_db):
        """Test that MongoDB errors are handled gracefully"""
        mock_get_mongo_db.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": self.today.strftime("%Y-%m-%d"),
            "end_date": self.today.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 500
        assert "Error fetching analytics" in response.json()["detail"]
    
    @patch('config.database.db.get_mongo_database')
    def test_zero_results(self, mock_get_mongo_db):
        """Test that zero results are handled correctly"""
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 0
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_db.return_value = mock_db
        
        response = client.get("/api/v1/analytics/service-requests/summary", params={
            "start_date": self.today.strftime("%Y-%m-%d"),
            "end_date": self.today.strftime("%Y-%m-%d"),
            "location": "NonExistentCity"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["done_count"] == 0
