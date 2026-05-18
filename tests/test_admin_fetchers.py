"""
Unit tests for individual admin fetchers.
Tests each provider-specific admin fetcher implementation.
"""

import pytest
from unittest.mock import Mock, patch
from app.fetchers.anthropic_admin import AnthropicAdminFetcher
from app.fetchers.openai_admin import OpenAIAdminFetcher
from app.fetchers.gemini_admin import GeminiAdminFetcher
from app.fetchers.deepseek_admin import DeepSeekAdminFetcher


class TestAnthropicAdminFetcher:
    """Test Anthropic admin fetcher."""
    
    def test_init_valid_admin_key(self):
        """Test initialization with valid admin key."""
        fetcher = AnthropicAdminFetcher("sk-ant-admin-test-key")
        
        assert fetcher.admin_key == "sk-ant-admin-test-key"
        assert fetcher.base_url == "https://api.anthropic.com/v1/organizations"
    
    def test_init_invalid_admin_key_raises_error(self):
        """Test that invalid admin key raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AnthropicAdminFetcher("sk-test-key")
        
        assert "Must use an Anthropic Admin key" in str(exc_info.value)
    
    def test_get_utilization_and_limits(self):
        """Test get_utilization_and_limits returns correct structure."""
        fetcher = AnthropicAdminFetcher("sk-ant-admin-test-key")
        
        # Mock the methods to avoid actual API calls
        with patch.object(fetcher, 'get_current_utilization', return_value={"tokens": 1000}), \
             patch.object(fetcher, 'get_rate_limits', return_value={"rpm": 500}):
            
            result = fetcher.get_utilization_and_limits()
            
            assert "utilization" in result
            assert "limits" in result
            assert "provider" in result
            assert "timestamp" in result
            assert result["utilization"] == {"tokens": 1000}
            assert result["limits"] == {"rpm": 500}
    
    @patch('app.fetchers.anthropic_admin.requests.get')
    def test_extract_live_rate_limits_success(self, mock_get):
        """Test successful extraction of rate limits from headers."""
        mock_response = Mock()
        mock_response.headers = {
            "anthropic-ratelimit-requests-limit": "60",
            "anthropic-ratelimit-requests-remaining": "50",
            "anthropic-ratelimit-input-tokens-limit": "32000",
            "anthropic-ratelimit-input-tokens-remaining": "30000",
            "anthropic-ratelimit-output-tokens-limit": "16000",
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        fetcher = AnthropicAdminFetcher("sk-ant-admin-test-key")
        limits = fetcher.extract_live_rate_limits()
        
        assert limits["requests_per_minute_limit"] == 60
        assert limits["requests_remaining"] == 50
        assert limits["input_tokens_per_minute_limit"] == 32000
        assert limits["input_tokens_remaining"] == 30000
        assert limits["output_tokens_per_minute_limit"] == 16000


class TestOpenAIAdminFetcher:
    """Test OpenAI admin fetcher."""
    
    def test_init(self):
        """Test initialization."""
        fetcher = OpenAIAdminFetcher("sk-test-key")
        
        assert fetcher.admin_key == "sk-test-key"
        assert fetcher.base_url == "https://api.openai.com/v1"
    
    def test_get_utilization_and_limits(self):
        """Test get_utilization_and_limits returns correct structure."""
        fetcher = OpenAIAdminFetcher("sk-test-key")
        
        with patch.object(fetcher, 'get_current_utilization', return_value={"tokens": 1000}), \
             patch.object(fetcher, 'get_rate_limits', return_value={"rpm": 500}):
            
            result = fetcher.get_utilization_and_limits()
            
            assert "utilization" in result
            assert "limits" in result
            assert "provider" in result
            assert "timestamp" in result


class TestGeminiAdminFetcher:
    """Test Gemini admin fetcher."""
    
    def test_init(self):
        """Test initialization."""
        fetcher = GeminiAdminFetcher("test-key")
        
        assert fetcher.admin_key == "test-key"
        assert fetcher.base_url == "https://generativelanguage.googleapis.com/v1beta"
    
    def test_get_utilization_and_limits(self):
        """Test get_utilization_and_limits returns correct structure."""
        fetcher = GeminiAdminFetcher("test-key")
        
        with patch.object(fetcher, 'get_current_utilization', return_value={"tokens": 1000}), \
             patch.object(fetcher, 'get_rate_limits', return_value={"rpm": 500}):
            
            result = fetcher.get_utilization_and_limits()
            
            assert "utilization" in result
            assert "limits" in result
            assert "provider" in result
            assert "timestamp" in result


class TestDeepSeekAdminFetcher:
    """Test DeepSeek admin fetcher."""
    
    def test_init(self):
        """Test initialization."""
        fetcher = DeepSeekAdminFetcher("test-key")
        
        assert fetcher.admin_key == "test-key"
        assert fetcher.base_url == "https://api.deepseek.com/v1"
    
    def test_get_utilization_and_limits(self):
        """Test get_utilization_and_limits returns correct structure."""
        fetcher = DeepSeekAdminFetcher("test-key")
        
        with patch.object(fetcher, 'get_current_utilization', return_value={"tokens": 1000}), \
             patch.object(fetcher, 'get_rate_limits', return_value={"rpm": 500}):
            
            result = fetcher.get_utilization_and_limits()
            
            assert "utilization" in result
            assert "limits" in result
            assert "provider" in result
            assert "timestamp" in result


class TestBaseAdminFetcherInterface:
    """Test that all fetchers implement the base interface correctly."""
    
    def test_anthropic_implements_base_interface(self):
        """Test Anthropic fetcher implements base interface."""
        fetcher = AnthropicAdminFetcher("sk-ant-admin-test-key")
        
        assert hasattr(fetcher, 'get_current_utilization')
        assert hasattr(fetcher, 'get_rate_limits')
        assert hasattr(fetcher, 'get_utilization_and_limits')
    
    def test_openai_implements_base_interface(self):
        """Test OpenAI fetcher implements base interface."""
        fetcher = OpenAIAdminFetcher("sk-test-key")
        
        assert hasattr(fetcher, 'get_current_utilization')
        assert hasattr(fetcher, 'get_rate_limits')
        assert hasattr(fetcher, 'get_utilization_and_limits')
    
    def test_gemini_implements_base_interface(self):
        """Test Gemini fetcher implements base interface."""
        fetcher = GeminiAdminFetcher("test-key")
        
        assert hasattr(fetcher, 'get_current_utilization')
        assert hasattr(fetcher, 'get_rate_limits')
        assert hasattr(fetcher, 'get_utilization_and_limits')
    
    def test_deepseek_implements_base_interface(self):
        """Test DeepSeek fetcher implements base interface."""
        fetcher = DeepSeekAdminFetcher("test-key")
        
        assert hasattr(fetcher, 'get_current_utilization')
        assert hasattr(fetcher, 'get_rate_limits')
        assert hasattr(fetcher, 'get_utilization_and_limits')
