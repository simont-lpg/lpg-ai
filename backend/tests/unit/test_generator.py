import pytest
from unittest.mock import patch, MagicMock
import httpx
from backend.app.generator import OllamaGenerator

def test_ollama_generator_http_error():
    """Test that OllamaGenerator handles HTTP errors gracefully."""
    generator = OllamaGenerator(
        api_url="http://localhost:11434",
        model_name="test-model"
    )
    
    # Mock httpx.stream to raise an HTTP error
    with patch('httpx.stream') as mock_stream:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response
        )
        mock_stream.return_value.__enter__.return_value = mock_response
        
        # Test generate method
        result = generator.generate("test prompt")
        assert result == "Model not available"
        
        # Test stream method
        stream_result = list(generator.stream("test prompt"))
        assert stream_result == ["Model not available"]

def test_ollama_generator_other_error():
    """Test that OllamaGenerator handles other errors gracefully."""
    generator = OllamaGenerator(
        api_url="http://localhost:11434",
        model_name="test-model"
    )
    
    # Mock httpx.stream to raise a generic error
    with patch('httpx.stream') as mock_stream:
        mock_stream.side_effect = Exception("Test error")
        
        # Test generate method
        result = generator.generate("test prompt")
        assert result == "Model not available"
        
        # Test stream method
        stream_result = list(generator.stream("test prompt"))
        assert stream_result == ["Model not available"] 