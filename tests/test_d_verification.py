"""Test D-task: Backend safety boundary for missing AI configuration."""
import pytest
from tarot_jupyterlab.errors import AIUnavailableError
from tarot_jupyterlab.ai.provider import OpenAICompatibleProvider


def test_missing_ai_config_raises_error():
    """If API key is missing, it should raise a friendly error, not crash."""
    # Simulate a scenario where no API Key is configured
    provider = OpenAICompatibleProvider(
        base_url="http://fake-url.com",
        model="test-model",
        api_key=""  # Empty Key
    )
    
    # We expect it to raise AIUnavailableError
    with pytest.raises(AIUnavailableError) as excinfo:
        provider.generate("Hello")
    
    # Verify the error message contains "No API key is configured"
    assert "No API key is configured" in str(excinfo.value)
