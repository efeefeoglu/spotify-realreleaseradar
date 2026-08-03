import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs

from spotify_auth import renew_refresh_token


class RenewRefreshTokenTests(unittest.TestCase):
    @patch("spotify_auth.urlopen")
    def test_exchanges_authorization_code(self, urlopen):
        response = Mock()
        response.read.return_value = b'{"refresh_token": "new-token"}'
        urlopen.return_value.__enter__.return_value = response

        token = renew_refresh_token("client", "secret", "code", "https://example.com/callback")

        self.assertEqual(token, "new-token")
        request = urlopen.call_args.args[0]
        request_data = parse_qs(request.data.decode())
        self.assertEqual(request_data["grant_type"], ["authorization_code"])
        self.assertEqual(request_data["code"], ["code"])
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 30)

    def test_rejects_missing_values(self):
        with self.assertRaisesRegex(ValueError, "authorization_code"):
            renew_refresh_token("client", "secret", "", "https://example.com/callback")

    @patch("spotify_auth.urlopen")
    def test_requires_refresh_token_in_response(self, urlopen):
        response = Mock()
        response.read.return_value = b'{"access_token": "short-lived"}'
        urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(RuntimeError, "did not include a refresh token"):
            renew_refresh_token("client", "secret", "code", "https://example.com/callback")


if __name__ == "__main__":
    unittest.main()
