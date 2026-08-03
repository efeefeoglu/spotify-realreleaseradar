"""Helpers for creating a new Spotify refresh token."""

import base64
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


def renew_refresh_token(client_id, client_secret, authorization_code, redirect_uri):
    """Exchange a one-time authorization code for a new refresh token.

    A revoked refresh token cannot itself be renewed. The account owner must
    authorize the application again and provide the resulting authorization
    code. Spotify requires ``redirect_uri`` to exactly match the URI used for
    that authorization request.
    """
    missing = [
        name
        for name, value in (
            ("client_id", client_id),
            ("client_secret", client_secret),
            ("authorization_code", authorization_code),
            ("redirect_uri", redirect_uri),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required value(s): {', '.join(missing)}")

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = Request(
        SPOTIFY_TOKEN_URL,
        data=urlencode({
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
        }).encode(),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        token_data = json.loads(response.read().decode())
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Spotify's token response did not include a refresh token")
    return refresh_token
