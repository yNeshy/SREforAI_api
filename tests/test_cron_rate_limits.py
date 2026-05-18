"""
Unit tests for cron job rate limits fetcher.
Tests the cron job that fetches and stores rate limit data.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from app.cron.rate_limits_fetcher import fetch_and_store_rate_limits, fetch_all_rate_limits


class TestFetchAndStoreRateLimits:
    """Test fetch_and_store_rate_limits function."""
    
    @patch('app.cron.rate_limits_fetchers.AdminFetcherFactory')
    def test_fetch_and_store_new_record(self, mock_factory):
        """Test creating a new rate limit cache record."""
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.get_utilization_and_limits.return_value = {
            "utilization": {"tokens": 1000},
            "limits": {"rpm": 500},
            "provider": "claude",
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_factory.create_fetcher.return_value = mock_fetcher
        
        # Mock no existing record
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Call function
        fetch_and_store_rate_limits(mock_db, "claude", "sk-ant-admin-test", "test-org-id")
        
        # Verify new record was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @patch('app.cron.rate_limits_fetchers.AdminFetcherFactory')
    def test_fetch_and_store_update_existing(self, mock_factory):
        """Test updating an existing rate limit cache record."""
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.get_utilization_and_limits.return_value = {
            "utilization": {"tokens": 2000},
            "limits": {"rpm": 600},
            "provider": "claude",
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_factory.create_fetcher.return_value = mock_fetcher
        
        # Mock existing record
        mock_cache = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cache
        
        # Call function
        fetch_and_store_rate_limits(mock_db, "claude", "sk-ant-admin-test", "test-org-id")
        
        # Verify existing record was updated
        assert mock_cache.utilization == {"tokens": 2000}
        assert mock_cache.limits == {"rpm": 600}
        mock_db.commit.assert_called_once()
    
    @patch('app.cron.rate_limits_fetchers.AdminFetcherFactory')
    def test_fetch_and_store_error_handling(self, mock_factory):
        """Test error handling when fetch fails."""
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock fetcher error
        mock_factory.create_fetcher.side_effect = Exception("API error")
        
        # Call function - should not raise, should rollback
        with pytest.raises(Exception):
            fetch_and_store_rate_limits(mock_db, "claude", "sk-ant-admin-test", "test-org-id")
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()


class TestFetchAllRateLimits:
    """Test fetch_all_rate_limits function."""
    
    @patch('app.cron.rate_limits_fetchers.get_db')
    @patch('app.cron.rate_limits_fetchers.fetch_and_store_rate_limits')
    def test_fetch_all_rate_limits_success(self, mock_fetch_store, mock_get_db):
        """Test fetching rate limits for all organizations."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        
        # Mock organizations
        mock_org = Mock()
        mock_org.id = "test-org-id"
        mock_org.openai_api_key_encrypted = "encrypted-key"
        mock_org.anthropic_api_key_encrypted = None
        mock_org.gemini_api_key_encrypted = None
        mock_org.deepseek_api_key_encrypted = None
        
        mock_db.query.return_value.all.return_value = [mock_org]
        
        # Mock encryption manager
        with patch('app.cron.rate_limits_fetchers.get_encryption_manager') as mock_get_enc:
            mock_enc = Mock()
            mock_enc.decrypt.return_value = "decrypted-key"
            mock_get_enc.return_value = mock_enc
            
            # Call function
            fetch_all_rate_limits()
            
            # Verify fetch_and_store was called for OpenAI
            mock_fetch_store.assert_called_once()
    
    @patch('app.cron.rate_limits_fetchers.get_db')
    def test_fetch_all_rate_limits_no_organizations(self, mock_get_db):
        """Test fetching when no organizations exist."""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        
        # Mock no organizations
        mock_db.query.return_value.all.return_value = []
        
        # Call function - should not raise
        fetch_all_rate_limits()
        
        # Verify close was called
        mock_db.close.assert_called_once()
