import json
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

from services.ollama_health import (
    OllamaHealthResult,
    check_ollama_health,
    check_ollama_model_available,
)


class OllamaHealthTest(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_check_health_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"models": []}).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = check_ollama_health("http://localhost:11434")

        self.assertTrue(result.reachable)
        self.assertTrue(result.server_ok)
        self.assertEqual(result.message, "Ollama 서버가 정상입니다.")

    @patch("urllib.request.urlopen")
    def test_check_health_connection_refused(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = check_ollama_health("http://localhost:11434")

        self.assertFalse(result.reachable)
        self.assertFalse(result.server_ok)
        self.assertEqual(result.message, "Ollama 서버가 실행되지 않았습니다.")

    @patch("urllib.request.urlopen")
    def test_check_health_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError()

        result = check_ollama_health("http://localhost:11434")

        self.assertFalse(result.reachable)
        self.assertFalse(result.server_ok)
        self.assertEqual(result.message, "Ollama 서버가 실행되지 않았습니다.")

    @patch("urllib.request.urlopen")
    def test_check_model_available(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"models": [{"name": "llama3.2:3b"}, {"name": "gemma:2b"}]}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = check_ollama_model_available("http://localhost:11434", "llama3.2:3b")

        self.assertTrue(result.reachable)
        self.assertTrue(result.server_ok)
        self.assertTrue(result.model_available)
        self.assertEqual(result.message, "모델 'llama3.2:3b'을(를) 사용할 수 있습니다.")

    @patch("urllib.request.urlopen")
    def test_check_model_missing(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"models": [{"name": "gemma:2b"}]}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = check_ollama_model_available("http://localhost:11434", "llama3.2:3b")

        self.assertTrue(result.reachable)
        self.assertTrue(result.server_ok)
        self.assertFalse(result.model_available)
        self.assertEqual(result.message, "모델 'llama3.2:3b'이(가) 설치되지 않았습니다.")

    @patch("urllib.request.urlopen")
    def test_check_model_prefix_match(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"models": [{"name": "llama3.2:3b:latest"}]}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = check_ollama_model_available("http://localhost:11434", "llama3.2:3b")

        self.assertTrue(result.model_available)

    @patch("urllib.request.urlopen")
    def test_check_model_server_down(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = check_ollama_model_available("http://localhost:11434", "llama3.2:3b")

        self.assertFalse(result.reachable)
        self.assertFalse(result.server_ok)
        self.assertIsNone(result.model_available)


if __name__ == "__main__":
    unittest.main()
