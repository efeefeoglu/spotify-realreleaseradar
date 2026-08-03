import os
import unittest
from unittest.mock import patch

from renew_refresh_token import required_env


class RequiredEnvTests(unittest.TestCase):
    @patch.dict(os.environ, {"PRESENT_SETTING": "configured"})
    def test_returns_configured_value(self):
        self.assertEqual(required_env("PRESENT_SETTING"), "configured")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_value_explains_github_environment(self):
        with self.assertRaisesRegex(
            RuntimeError, "GitHub environment selected for this workflow run"
        ):
            required_env("SPOTIFY_CLIENT_ID")


if __name__ == "__main__":
    unittest.main()
