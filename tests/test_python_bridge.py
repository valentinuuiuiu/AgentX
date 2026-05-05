import os
import pytest
from unittest.mock import patch, Mock
from core.python_bridge import get_deepseek_reasoning
import requests

def test_get_deepseek_reasoning_success():
    market_data = {"price": 100}
    ta_signals = {"rsi": 30}

    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "The market is oversold. Consider buying."
                }
            }
        ]
    }

    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test_key"}):
        with patch("core.python_bridge.requests.post", return_value=mock_response) as mock_post:
            result = get_deepseek_reasoning(market_data, ta_signals)

            assert result == "The market is oversold. Consider buying."
            mock_post.assert_called_once_with(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer test_key",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a financial analyst AI."},
                        {"role": "user", "content": "Analyze this market data: {'price': 100} and these technical signals: {'rsi': 30}."}
                    ]
                }
            )

def test_get_deepseek_reasoning_api_error():
    market_data = {"price": 100}
    ta_signals = {"rsi": 30}

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")

    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test_key"}):
        with patch("core.python_bridge.requests.post", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError, match="API Error"):
                get_deepseek_reasoning(market_data, ta_signals)
