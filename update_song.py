#!/usr/bin/env python3
"""
Update makko.json with song-of-the-day info from a Tidal track URL.

Usage:
    python3 update_song.py <tidal_url>

Example:
    python3 update_song.py https://tidal.com/browse/track/251380836

Environment variables (required):
    TIDAL_CLIENT_ID     - Your Tidal API client ID
    TIDAL_CLIENT_SECRET - Your Tidal API client secret

    Register an app at https://developer.tidal.com to obtain these credentials.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse
import base64

import os
from dotenv import load_dotenv

load_dotenv('.env')

MAKKO_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "makko.json")
TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
API_BASE = "https://openapi.tidal.com/v2"


def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def extract_track_id(url):
    """Extract the numeric track ID from various Tidal URL formats."""
    # Matches: tidal.com/browse/track/123, tidal.com/track/123, etc.
    match = re.search(r"tidal\.com/(?:browse/)?track/(\d+)", url)
    if match:
        return match.group(1)
    # Maybe the user just passed a raw track ID
    if url.strip().isdigit():
        return url.strip()
    return None


def get_access_token(client_id, client_secret):
    """Obtain a client-credentials access token from the Tidal auth endpoint."""
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["access_token"]
    except Exception as e:
        die(f"Failed to authenticate with Tidal API: {e}")


def api_get(path, token, params=None):
    """Make a GET request to the Tidal API."""
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        die(f"Tidal API request failed ({e.code}): {body}")


def extract_artwork_url(included):
    """Extract the largest artwork image URL from included artwork resources."""
    for item in included:
        if item.get("type") == "artworks":
            files = item.get("attributes", {}).get("files", [])
            if files:
                # Pick the largest image by width
                best = sorted(
                    files, key=lambda x: x.get("meta", {}).get("width", 0), reverse=True
                )[0]
                return best.get("href", "")
    return ""


def get_track_info(track_id, token):
    """Fetch track title, artist name, and album art URL from the Tidal API."""
    # Get track details with included artists and albums (JSON:API format)
    track = api_get(
        f"/tracks/{track_id}",
        token,
        {"countryCode": "US", "include": "artists,albums"},
    )

    attributes = track.get("data", {}).get("attributes", {})
    title = attributes.get("title", "Unknown")
    artist_name = "Unknown"
    album_art_url = ""

    # Parse included resources for artist name
    included = track.get("included", [])
    for item in included:
        if item.get("type") == "artists" and artist_name == "Unknown":
            artist_name = item.get("attributes", {}).get("name", "Unknown")

    # If artists weren't included, fetch them separately
    if artist_name == "Unknown":
        relationships = track.get("data", {}).get("relationships", {})
        artists_rel = relationships.get("artists", {}).get("data", [])
        if artists_rel:
            try:
                artist_data = api_get(
                    f"/artists/{artists_rel[0]['id']}",
                    token,
                    {"countryCode": "US"},
                )
                artist_name = (
                    artist_data.get("data", {})
                    .get("attributes", {})
                    .get("name", "Unknown")
                )
            except SystemExit:
                pass

    # Fetch album cover art via the coverArt relationship (artworks endpoint)
    relationships = track.get("data", {}).get("relationships", {})
    albums_rel = relationships.get("albums", {}).get("data", [])
    if not albums_rel:
        # Check included albums for their ID
        for item in included:
            if item.get("type") == "albums":
                albums_rel = [{"id": item["id"]}]
                break

    if albums_rel:
        try:
            album_data = api_get(
                f"/albums/{albums_rel[0]['id']}",
                token,
                {"countryCode": "US", "include": "coverArt"},
            )
            album_art_url = extract_artwork_url(
                album_data.get("included", [])
            )
        except SystemExit:
            pass

    return title, artist_name, album_art_url


def update_makko(song_url, title, artist, album_art_url):
    """Update the song_of_the_day section in makko.json."""
    try:
        with open(MAKKO_JSON, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        die(f"Could not find {MAKKO_JSON}")
    except json.JSONDecodeError as e:
        die(f"Invalid JSON in {MAKKO_JSON}: {e}")

    if "custom" not in data:
        data["custom"] = {}

    data["custom"]["song_of_the_day"] = {
        "album_art_url": album_art_url,
        "song_url": song_url,
        "song_title": title,
        "song_artist": artist,
    }

    with open(MAKKO_JSON, "w") as f:
        json.dump(data, f, indent="\t", ensure_ascii=False)
        f.write("\n")

    print(f"Updated {MAKKO_JSON}:")
    print(f"  Artist:    {artist}")
    print(f"  Title:     {title}")
    print(f"  Album Art: {album_art_url}")
    print(f"  URL:       {song_url}")


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip())
        sys.exit(1)

    tidal_url = sys.argv[1]
    track_id = extract_track_id(tidal_url)
    if not track_id:
        die(
            "Could not extract track ID from URL.\n"
            "Expected format: https://tidal.com/browse/track/<id>"
        )

    client_id = os.environ.get("TIDAL_CLIENT_ID", "").strip()
    client_secret = os.environ.get("TIDAL_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        die(
            "Missing Tidal API credentials.\n"
            "Set TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET environment variables.\n"
            "Register an app at https://developer.tidal.com to get these."
        )

    # Normalize the URL to a consistent format
    song_url = f"https://tidal.com/track/{track_id}"

    print(f"Fetching metadata for track {track_id}...")
    token = get_access_token(client_id, client_secret)
    title, artist, album_art_url = get_track_info(track_id, token)
    update_makko(song_url, title, artist, album_art_url)


if __name__ == "__main__":
    main()
