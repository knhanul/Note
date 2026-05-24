import json
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

from services.ai_llm_client import LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_prompt_builder import RagPromptPayload
from services.ollama_llm_client import OllamaLlmClient


class OllamaLlmClientTest(unittest.TestCase):
    def _make_client(self):
        return OllamaLlmClient(base_url="http://localhost:11434", default_model="llama3.2:3b")

    @patch("urllib.request.urlopen")
    def test_generate_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"response": "답변입니다", "model": "llama3.2:3b"}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = self._make_client()
        result = client.generate("system", "user question")

        self.assertEqual(result.text, "답변입니다")
        self.assertEqual(result.provider, "ollama")
        self.assertIsNotNone(result.raw)
        self.assertEqual(result.raw["response"], "답변입니다")

    @patch("urllib.request.urlopen")
    def test_generate_from_payload(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"response": "답변", "model": "llama3.2:3b"}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = self._make_client()
        payload = RagPromptPayload(
            system_prompt="system prompt",
            user_prompt="user prompt",
            context_text="context",
            sources=[],
            warnings=[],
            total_chars=100,
        )
        result = client.generate_from_payload(payload)

        self.assertEqual(result.text, "답변")
        self.assertEqual(result.provider, "ollama")

    @patch("urllib.request.urlopen")
    def test_connection_failure(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        client = self._make_client()
        result = client.generate("system", "user")

        self.assertEqual(result.text, "")
        self.assertIn("[OLLAMA_CONNECTION_FAILED]", result.warnings)

    @patch("urllib.request.urlopen")
    def test_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError()

        client = self._make_client()
        result = client.generate("system", "user")

        self.assertEqual(result.text, "")
        self.assertIn("[OLLAMA_TIMEOUT]", result.warnings)

    @patch("urllib.request.urlopen")
    def test_invalid_json(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = self._make_client()
        result = client.generate("system", "user")

        self.assertEqual(result.text, "")
        self.assertIn("[OLLAMA_INVALID_JSON]", result.warnings)

    @patch("urllib.request.urlopen")
    def test_missing_response_field(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"model": "llama3.2:3b"}).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = self._make_client()
        result = client.generate("system", "user")

        self.assertEqual(result.text, "")
        self.assertIn("[OLLAMA_EMPTY_RESPONSE]", result.warnings)

    @patch("urllib.request.urlopen")
    def test_options_model_override(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"response": "답변", "model": "custom-model"}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = self._make_client()
        options = LlmGenerateOptions(model="custom-model", temperature=0.5)
        result = client.generate("system", "user", options)

        self.assertEqual(result.model, "custom-model")

    @patch("urllib.request.urlopen")
    def test_temperature_option_included(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"response": "답변", "model": "llama3.2:3b"}
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = self._make_client()
        options = LlmGenerateOptions(model="llama3.2:3b", temperature=0.7)
        result = client.generate("system", "user", options)

        self.assertEqual(result.text, "답변")

    def test_no_real_network(self):
        client = self._make_client()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
            result = client.generate("system", "user")
            self.assertEqual(result.text, "")
            self.assertIn("[OLLAMA_CONNECTION_FAILED]", result.warnings)


if __name__ == "__main__":
    unittest.main()
