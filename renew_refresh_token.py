"""Exchange a Spotify authorization code and expose the token to Actions."""

import os

from spotify_auth import renew_refresh_token


def main():
    refresh_token = renew_refresh_token(secrets.SPOTIFY_CLIENT_ID,secrets.SPOTIFY_CLIENT_SECRET,secrets.SPOTIFY_AUTHORIZATION_CODE,secrets.SPOTIFY_REDIRECT_URI)

    # Mask the credential before making it available to later workflow steps.
    print(f"::add-mask::{refresh_token}")
    output_path = required_env("GITHUB_OUTPUT")
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"refresh_token={refresh_token}\n")


if __name__ == "__main__":
    main()
