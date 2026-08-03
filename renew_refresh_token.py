"""Exchange a Spotify authorization code and expose the token to Actions."""

import os

from spotify_auth import renew_refresh_token

def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


spotify_client_id = required_env("SPOTIFY_CLIENT_ID")
spotify_client_secret = required_env("SPOTIFY_CLIENT_SECRET")
spotify_refresh_token = required_env("SPOTIFY_REFRESH_TOKEN")


def main():
    refresh_token = renew_refresh_token(required_env("SPOTIFY_CLIENT_ID"),required_env("SPOTIFY_CLIENT_SECRET"),required_env("SPOTIFY_AUTHORIZATION_CODE"),required_env("SPOTIFY_REDIRECT_URI"))

    # Mask the credential before making it available to later workflow steps.
    print(f"::add-mask::{refresh_token}")
    output_path = required_env("GITHUB_OUTPUT")
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"refresh_token={refresh_token}\n")


if __name__ == "__main__":
    main()
