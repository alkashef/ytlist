#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env
config_dir = Path(__file__).parent / "config"
env_file = config_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

API = "https://www.googleapis.com/youtube/v3"

def http_get(url, params):
    """Perform an HTTP GET request with query parameters.
    
    Args:
        url: The base URL to make the request to.
        params: Dictionary of query parameters to include in the request.
    
    Returns:
        dict: Parsed JSON response from the API.
    """
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    with urllib.request.urlopen(f"{url}?{qs}") as r:
        return json.loads(r.read().decode("utf-8"))

def parse_channel_ref(channel_url: str):
    """Parse a YouTube channel URL and extract the channel identifier.
    
    Args:
        channel_url: YouTube channel URL (e.g., /channel/<id> or /@<handle>).
    
    Returns:
        tuple: A tuple of (kind, value) where kind is either 'id' or 'handle'.
    
    Raises:
        SystemExit: If the channel URL format is not supported.
    """
    u = urllib.parse.urlparse(channel_url)
    path = u.path.strip("/")
    parts = path.split("/")

    if len(parts) >= 2 and parts[0] == "channel":
        return ("id", parts[1])

    if parts and parts[0].startswith("@"):
        return ("handle", parts[0][1:])

    raise SystemExit("Unsupported channel URL. Use /channel/<id> or /@<handle>.")

def iso8601_duration_to_seconds(dur: str) -> int:
    """Convert ISO 8601 duration format to seconds.
    
    Args:
        dur: Duration string in ISO 8601 format (e.g., 'PT1H30M45S').
    
    Returns:
        int: Total duration in seconds.
    """
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur)
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mi = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mi * 60 + s

def get_channel_id_and_uploads_playlist(api_key: str, channel_url: str):
    """Retrieve the channel ID and uploads playlist ID for a given channel.
    
    Args:
        api_key: YouTube Data API key.
        channel_url: YouTube channel URL.
    
    Returns:
        tuple: A tuple of (channel_id, uploads_playlist_id).
    
    Raises:
        SystemExit: If the channel is not found or the API key is invalid.
    """
    kind, val = parse_channel_ref(channel_url)

    params = {"part": "id,contentDetails", "key": api_key}
    if kind == "id":
        params["id"] = val
    else:
        params["forHandle"] = val

    data = http_get(f"{API}/channels", params)
    items = data.get("items", [])
    if not items:
        raise SystemExit("Channel not found (check URL / key).")

    ch = items[0]
    return ch["id"], ch["contentDetails"]["relatedPlaylists"]["uploads"]

def iter_upload_video_ids(api_key: str, uploads_playlist_id: str):
    """Iterate through all video IDs in a channel's uploads playlist.
    
    Args:
        api_key: YouTube Data API key.
        uploads_playlist_id: Playlist ID for the channel's uploads.
    
    Yields:
        str: Video ID from the uploads playlist.
    """
    token = None
    while True:
        data = http_get(f"{API}/playlistItems", {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
            "pageToken": token,
            "key": api_key,
        })
        for it in data.get("items", []):
            yield it["contentDetails"]["videoId"]
        token = data.get("nextPageToken")
        if not token:
            break

def chunks(xs, n=50):
    """Split an iterable into chunks of a specified size.
    
    Args:
        xs: Iterable to be chunked.
        n: Size of each chunk (default: 50).
    
    Yields:
        list: Chunk of items from the iterable.
    """
    buf = []
    for x in xs:
        buf.append(x)
        if len(buf) == n:
            yield buf
            buf = []
    if buf:
        yield buf

def fetch_video_rows(api_key: str, video_ids, min_duration):
    """Fetch video details and filter based on criteria.
    
    Excludes livestreams and videos below the minimum duration (e.g., Shorts).
    
    Args:
        api_key: YouTube Data API key.
        video_ids: Iterable of video IDs to fetch.
        min_duration: Minimum video duration in seconds to include.
    
    Yields:
        tuple: A tuple of (title, url, duration_in_minutes, date) for each video.
    """
    for batch in chunks(video_ids, 50):
        data = http_get(f"{API}/videos", {
            "part": "snippet,contentDetails,liveStreamingDetails",
            "id": ",".join(batch),
            "maxResults": 50,
            "key": api_key,
        })
        for v in data.get("items", []):
            # Exclude livestreams/past livestreams
            if "liveStreamingDetails" in v:
                continue

            vid = v["id"]
            sn = v.get("snippet", {})
            cd = v.get("contentDetails", {})

            secs = iso8601_duration_to_seconds(cd.get("duration", "PT0S"))
            # Exclude Shorts heuristic: duration threshold
            if secs < min_duration:
                continue

            title = (sn.get("title") or "").replace("\n", " ").strip()
            url = f"https://www.youtube.com/watch?v={vid}"
            published_at = sn.get("publishedAt") or ""
            date = published_at[:10] if len(published_at) >= 10 else published_at

            yield (title, url, round(secs / 60), date)

def main():
    """Main function to export YouTube channel videos to CSV.
    
    Parses command-line arguments, fetches video data from YouTube API,
    and writes filtered results to a CSV file (excluding Shorts and livestreams).
    """
    ap = argparse.ArgumentParser(description="Export YouTube channel regular videos to CSV (no Shorts, no livestreams).")
    ap.add_argument("channel_url", nargs="?", default=os.environ.get("DEFAULT_CHANNEL"), help="Channel URL: https://www.youtube.com/@handle or https://www.youtube.com/channel/UCxxxx (default: DEFAULT_CHANNEL from env)")
    ap.add_argument("--key", default=os.environ.get("YOUTUBE_API_KEY"), help="YouTube Data API key (or env YOUTUBE_API_KEY)")
    ap.add_argument("--out", default=os.environ.get("DEFAULT_OUT", "-"), help="Output CSV path (default: DEFAULT_OUT from env or stdout)")
    ap.add_argument("--min-duration", type=int, default=int(os.environ.get("DEFAULT_MIN_DURATION", "2")) * 60, help="Minimum duration in seconds (default: DEFAULT_MIN_DURATION from env in minutes or 2)")
    args = ap.parse_args()

    if not args.key:
        raise SystemExit("Missing API key. Provide --key or set YOUTUBE_API_KEY.")

    if not args.channel_url:
        raise SystemExit("Missing channel URL. Provide a URL argument or set DEFAULT_CHANNEL.")

    _, uploads = get_channel_id_and_uploads_playlist(args.key, args.channel_url)

    out_f = sys.stdout if args.out == "-" else open(args.out, "w", newline="", encoding="utf-8")
    w = csv.writer(out_f)
    w.writerow(["Title", "URL", "Length (min)", "Date"])

    # Newest-first: uploads playlist is typically newest-first already.
    video_ids = iter_upload_video_ids(args.key, uploads)
    count = 0
    for row in fetch_video_rows(args.key, video_ids, args.min_duration):
        w.writerow(row)
        count += 1

    if out_f is not sys.stdout:
        out_f.close()
    
    print(f"Wrote {count} videos to CSV", file=sys.stderr)

if __name__ == "__main__":
    main()
