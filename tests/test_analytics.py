import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pytz
from routes.analytics import get_service_requests_summary

class TestAnalyticsService:
    
    @patch('routes.analytics.db.get_mongo_database')
    def test_get_done_count_with_date_range(self, mock_get_mongo_db):
        """Test that done count is correctly filtered by date range"""
        # Mock MongoDB collection
        mock_collection = Mock()
        mock_collection.count_documents.return_value = 42
        mock_db = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_get_mongo_db.return_value = mock_db
        
        # Test with date range
        result = get_service_requests_summary(
            range="last_7",
            start_date="2025-01-01",
            end_date="2025-01-07",
            location="Kolkata"
        )
        
        # Verify the call was made with correct filter
        mock_collection.count_documents.assert_called_once()
        call_args = mock_collection.count_documents.call_args[0][0]
        
        # Check that the filter includes done status and location
        assert call_args["status.done.check"] == True
        assert call_args["location"]["$eq"] == "Kolkata"
        assert "date" in call_args
        assert "$gte" in call_args["date"]
        assert "$lte" in call_args["date"]
        
        # Check response format
        assert result == {"done_count": 42}
    
    @patch('routes.analytics.db.get_mongo_database')
    def test_get_done_count_all_cities(self, mock_get_mongo_db):
        """Test that 'All Cities' location filter is ignored"""
        # Mock MongoDB collection
        mock_collection = Mock()
        mock_collection.count_documents.return_value = 100
        mock_db = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_get_mongo_db.return_value = mock_db
        
        # Test with "All Cities" location
        result = get_service_requests_summary(
            range="today",
            start_date="2025-01-01",
            end_date="2025-01-01",
            location="All Cities"
        )
        
        # Verify the call was made without location filter
        call_args = mock_collection.count_documents.call_args[0][0]
        assert "location" not in call_args
        assert result == {"done_count": 100}
    
    @patch('routes.analytics.db.get_mongo_database')
    def test_get_done_count_empty_location(self, mock_get_mongo_db):
        """Test that empty location filter is ignored"""
        # Mock MongoDB collection
        mock_collection = Mock()
        mock_collection.count_documents.return_value = 50
        mock_db = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_get_mongo_db.return_value = mock_db
        
        # Test with empty location
        result = get_service_requests_summary(
            range="yesterday",
            start_date="2025-01-01",
            end_date="2025-01-01",
            location=""
        )
        
        # Verify the call was made without location filter
        call_args = mock_collection.count_documents.call_args[0][0]
        assert "location" not in call_args
        assert result == {"done_count": 50}
    
    @patch('routes.analytics.db.get_mongo_database')
    def test_get_done_count_specific_city(self, mock_get_mongo_db):
        """Test that specific city location filter is applied"""
        # Mock MongoDB collection
        mock_collection = Mock()
        mock_collection.count_documents.return_value = 25
        mock_db = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_get_mongo_db.return_value = mock_db
        
        # Test with specific city using start_date/end_date parameters
        result = get_service_requests_summary(
            range="custom",
            start="2025-01-01",
            end="2025-01-07",
            location="Mumbai",
            start_date="2025-01-01",
            end_date="2025-01-07"
        )
        
        # Verify the call was made with location filter
        call_args = mock_collection.count_documents.call_args[0][0]
        assert call_args["location"]["$eq"] == "Mumbai"
        assert result == {"done_count": 25}
