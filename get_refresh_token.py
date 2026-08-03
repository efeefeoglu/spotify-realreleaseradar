#!/usr/bin/env python3
"""Run Spotify's OAuth authorization-code flow on a local computer."""

import argparse
import html
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from requests.auth import HTTPBasicAuth


AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
DEFAULT_SCOPES = (
    "playlist-read-private",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-follow-read",
    "user-follow-modify",
    "user-read-recently-played",
)


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def authorization_url(client_id, redirect_uri, state):
    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": " ".join(DEFAULT_SCOPES),
            "show_dialog": "true",
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def callback_handler(expected_state, result, received):
    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            if not secrets.compare_digest(query.get("state", [""])[0], expected_state):
                self._reply(400, "OAuth state did not match. Close this tab and try again.")
                result["error"] = "OAuth state did not match"
            elif "error" in query:
                message = query["error"][0]
                self._reply(400, f"Spotify authorization failed: {message}")
                result["error"] = message
            elif "code" not in query:
                self._reply(400, "Spotify did not return an authorization code.")
                result["error"] = "Missing authorization code"
            else:
                result["code"] = query["code"][0]
                self._reply(200, "Authorization complete. You can close this tab.")
            received.set()

        def _reply(self, status, message):
            body = (
                "<!doctype html><html><body><h1>Spotify authorization</h1>"
                f"<p>{html.escape(message)}</p></body></html>"
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return OAuthCallbackHandler


def receive_authorization_code(port, state, timeout):
    result = {}
    received = threading.Event()
    server = HTTPServer(
        ("127.0.0.1", port), callback_handler(state, result, received)
    )
    server.timeout = timeout
    server.handle_request()
    server.server_close()

    if not received.is_set():
        raise RuntimeError(f"Timed out after {timeout} seconds waiting for Spotify")
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["code"]


def exchange_code(client_id, client_secret, code, redirect_uri):
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        auth=HTTPBasicAuth(client_id, client_secret),
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        detail = response.text.strip()
        raise RuntimeError(f"Spotify token exchange failed: {detail}") from error

    refresh_token = response.json().get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Spotify's token response did not contain a refresh token")
    return refresh_token


def parse_args():
    parser = argparse.ArgumentParser(
        description="Authorize this project and print a new Spotify refresh token."
    )
    parser.add_argument("--port", type=int, default=8888, help="callback port (default: 8888)")
    parser.add_argument(
        "--timeout", type=int, default=300, help="login timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="print the login URL without opening a browser",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    client_id = required_env("SPOTIFY_CLIENT_ID")
    client_secret = required_env("SPOTIFY_CLIENT_SECRET")
    redirect_uri = f"http://127.0.0.1:{args.port}/callback"
    state = secrets.token_urlsafe(32)
    login_url = authorization_url(client_id, redirect_uri, state)

    print(f"Listening for Spotify at {redirect_uri}")
    print("This exact URI must be registered in your Spotify app settings.")
    print(f"\nOpen this URL to log in:\n{login_url}\n")
    if not args.no_browser and not webbrowser.open(login_url):
        print("Could not open a browser automatically; use the URL above.")

    code = receive_authorization_code(args.port, state, args.timeout)
    refresh_token = exchange_code(client_id, client_secret, code, redirect_uri)
    print("\nAuthorization succeeded. Set this secret in your local environment and CI:")
    print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, requests.RequestException) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
