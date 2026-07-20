from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.providers.groq_provider import GroqProvider


class GroqProviderFallbackTests(unittest.TestCase):
    def test_generate_json_returns_fallback_payload_for_auth_errors(self) -> None:
        provider = GroqProvider()
        provider._client = MagicMock()
        provider._client.chat.completions.create.side_effect = RuntimeError("401 invalid_api_key")

        payload = provider.generate_json(
            "Analyze Nike for ERP readiness.",
            system_prompt="Return summary, digital_maturity, business_challenges, erp_opportunities",
        )

        self.assertIn("summary", payload)
        self.assertIn("digital_maturity", payload)
        self.assertIn("business_challenges", payload)
        self.assertIn("erp_opportunities", payload)
        self.assertGreaterEqual(payload["confidence_score"], 0.0)
        self.assertLessEqual(payload["confidence_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
