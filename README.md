# Spotify Real Release Radar

Spotify Real Release Radar is a small automation script that builds a more
personal release-discovery playlist from the artists represented in your own
Spotify library.

Unlike Spotify's built-in Release Radar, the script combines artists from a
long-term "Ultimate" playlist with artists that appear repeatedly in your
recent listening. It then finds their releases from the last 30 days, adds up
to two tracks per release to a dedicated playlist, and supplements those tracks
with music from related artists.

## What the weekly job does

In one run, `main.py`:

1. Removes albums represented in the **Adeu** playlist from the **Yeni**
   playlist, then clears Adeu.
2. Clears the generated **Real Release Radar** and **Mas Nuevos** playlists.
3. Builds a source artist list from the **Ultimate** playlist and artists heard
   at least three times in the 50 most recently played tracks.
4. Follows source artists that the Spotify account does not already follow.
5. Adds tracks from source-artist releases published within the last 30 days to
   Real Release Radar.
6. Adds up to two top tracks from related artists recommended by at least two
   source artists.
7. Fills Mas Nuevos with 25 randomly selected tracks from Yeni.

> [!WARNING]
> The script changes playlists in place. Real Release Radar and Mas Nuevos are
> cleared before they are rebuilt, and tracks referenced by Adeu are removed
> from Yeni. Use dedicated playlists and verify every playlist ID before the
> first run.

## Configuration

The script reads all credentials and playlist IDs from environment variables.
Copy the example file and fill in your own values:

```bash
cp .env.example .env
```

| Variable | Required | Purpose |
| --- | --- | --- |
| `SPOTIFY_CLIENT_ID` | Yes | Spotify application client ID. |
| `SPOTIFY_CLIENT_SECRET` | Yes | Spotify application client secret. |
| `SPOTIFY_REFRESH_TOKEN` | Yes | User refresh token used to obtain an access token. |
| `SPOTIFY_ADEU_PLAYLIST_ID` | Yes | Staging playlist whose albums should leave Yeni. |
| `SPOTIFY_YENI_PLAYLIST_ID` | Yes | Pool of new music used by Adeu and Mas Nuevos. |
| `SPOTIFY_RELEASE_RADAR_PLAYLIST_ID` | Yes | Destination rebuilt with recent and related releases. |
| `SPOTIFY_MASNUEVOS_PLAYLIST_ID` | Yes | Destination rebuilt with a random Yeni selection. |
| `SPOTIFY_ULTIMATE_PLAYLIST_ID` | Yes | Long-term playlist used to discover source artists. |
| `SPOTIFY_EXCLUDED_ARTIST_IDS` | No | Comma-separated artist IDs excluded from recent-listening discovery. |

The refresh token must belong to the account that owns or can edit the target
playlists and must authorize the Spotify operations used by the script,
including reading recently played music, reading and changing followed artists,
and reading and modifying the configured playlists.

Keep `.env`, client secrets, and refresh tokens out of version control. The
included example contains names only and is safe to copy as a template.

## Run locally

Python 3.10 or later is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install requests
set -a
source .env
set +a
python main.py
```

Because the script calls the live Spotify API and immediately updates
playlists, there is no dry-run mode. Test with disposable playlists first.

## GitHub Actions

The workflow in `.github/workflows/weekly.yml` runs every Friday at 05:25 UTC
and can also be started manually with **Run workflow**.

Configure these repository settings before running it:

- Add every setting shown above as a GitHub Actions **secret**, using the same
  names. The optional `SPOTIFY_EXCLUDED_ARTIST_IDS` secret may be omitted.

### Replace a revoked refresh token

A revoked refresh token cannot be used to obtain another refresh token. First,
authorize the Spotify application again with an authorization URL containing
the required scopes and `response_type=code`. The redirect URI must exactly
match one registered in the Spotify application dashboard. Copy the `code`
query parameter from the redirect URL promptly; it is short-lived and can only
be used once.

To safely exchange that code and replace the repository secret:

1. Put `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
   `SPOTIFY_AUTHORIZATION_CODE`, and `GH_SECRETS_TOKEN` in the same GitHub
   environment. Also set `SPOTIFY_REDIRECT_URI` as a secret in that environment
   with the exact redirect URI used in the authorization request.
2. Give `GH_SECRETS_TOKEN` permission to write Actions secrets for this
   repository. The workflow's built-in `GITHUB_TOKEN` cannot manage repository
   secrets.
3. Do not put the one-time authorization code in a workflow-dispatch text
   input. Store it as `SPOTIFY_AUTHORIZATION_CODE` instead.
4. Run **Renew Spotify refresh token** from the Actions tab and select the
   GitHub environment containing the settings. GitHub does not expose an
   environment secret unless the job declares that environment; an empty
   secret expression otherwise becomes an empty environment variable.
5. Delete the now-used `SPOTIFY_AUTHORIZATION_CODE` secret after the workflow
   succeeds.

The workflow calls `renew_refresh_token.py`, masks the returned credential, and
uses GitHub CLI to replace `SPOTIFY_REFRESH_TOKEN`. The next weekly run then
uses the new token. Keep `GH_SECRETS_TOKEN` narrowly scoped. Alternatively, run
the helper locally and update `SPOTIFY_REFRESH_TOKEN` manually through the
repository settings.

GitHub Actions can exchange an authorization code for a refresh token, but it
cannot perform Spotify's interactive user-consent step for you. Obtain the
one-time authorization code in a browser first. Also note that this workflow
replaces a missing or revoked refresh token; routine runs should reuse the
existing refresh token to request short-lived access tokens rather than create
a new refresh token every week.

The authorization request must include the scopes needed by `main.py`:
`user-read-recently-played`, `user-follow-read`, `user-follow-modify`,
`playlist-read-private`, `playlist-modify-private`, and
`playlist-modify-public`.

## Operational notes

- Only the first artist credited on tracks in Ultimate and recently played
  albums is used for source-artist discovery.
- A recent release is considered eligible when its full `YYYY-MM-DD` release
  date is fewer than 30 days old.
- Spotify API errors are printed to the workflow log; there is currently no
  retry or rollback mechanism.
- Yeni must contain at least 25 tracks for the random Mas Nuevos selection.
