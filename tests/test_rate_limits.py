"""
Unit tests for rate limits endpoint.
Tests the rate limits API endpoint that reads from database.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api.schemas import RateLimitRequest, RateLimitResponse
from app.models.rate_limits import RateLimitCache


class TestRateLimitsEndpoint:
    """Test rate limits endpoint."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    @patch('app.api.v1.rate_limits.get_db')
    def test_rate_limits_success(self, mock_get_db):
        """Test successful rate limits fetch from database."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        
        # Mock cached data
        mock_cache = Mock()
        mock_cache.provider = "claude"
        mock_cache.api_key_id = "sk-ant-admin-test"
        mock_cache.utilization = {"tokens_used_last_24h": 1000}
        mock_cache.limits = {"rpm_limit": 500}
        mock_cache.updated_at = Mock()
        mock_cache.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cache
        
        # Make request
        response = self.client.post(
            "/api/v1/rate-limits",
            json={
                "provider": "claude",
                "api_key": "sk-ant-admin-test"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["utilization"]["tokens_used_last_24h"] == 1000
        assert data["limits"]["rpm_limit"] == 500
        assert data["provider"] == "claude"
    
    @patch('app.api.v1.rate_limits.get_db')
    def test_rate_limits_not_found(self, mock_get_db):
        """Test rate limits when no cached data exists."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        
        # Mock no cached data
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = self.client.post(
            "/api/v1/rate-limits",
            json={
                "provider": "claude",
                "api_key": "sk-ant-admin-test"
            }
        )
        
        assert response.status_code == 404
        assert "No cached rate limit data found" in response.json()["detail"]
    
    def test_rate_limits_validation_error_missing_provider(self):
        """Test rate limits with missing provider field."""
        response = self.client.post(
            "/api/v1/rate-limits",
            json={
                "api_key": "test-key"
            }
        )
        
        assert response.status_code == 422
    
    def test_rate_limits_validation_error_missing_api_key(self):
        """Test rate limits with missing api_key field."""
        response = self.client.post(
            "/api/v1/rate-limits",
            json={
                "provider": "claude"
            }
        )
        
        assert response.status_code == 422
    
    def test_rate_limits_validation_error_invalid_provider(self):
        """Test rate limits with invalid provider value."""
        response = self.client.post(
            "/api/v1/rate-limits",
            json={
                "provider": "invalid",
                "api_key": "test-key"
            }
        )
        
        assert response.status_code == 422


class TestRateLimitsSchemas:
    """Test rate limits Pydantic schemas."""
    
    def test_rate_limit_request_valid(self):
        """Test valid RateLimitRequest schema."""
        request = RateLimitRequest(
            provider="claude",
            api_key="sk-ant-admin-test"
        )
        
        assert request.provider == "claude"
        assert request.api_key == "sk-ant-admin-test"
    
    def test_rate_limit_request_invalid_provider(self):
        """Test RateLimitRequest with invalid provider."""
        with pytest.raises(ValueError):
            RateLimitRequest(
                provider="invalid",
                api_key="test-key"
            )
    
    def test_rate_limit_response_valid(self):
        """Test valid RateLimitResponse schema."""
        response = RateLimitResponse(
            utilization={"tokens": 1000},
            limits={"rpm": 500},
            provider="claude",
            timestamp="2024-01-01T00:00:00"
        )
        
        assert response.utilization == {"tokens": 1000}
        assert response.limits == {"rpm": 500}
        assert response.provider == "claude"
