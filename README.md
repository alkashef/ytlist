# ytdump (YouTube Channel CSV Exporter)

Export all regular videos from a YouTube channel to CSV (title, URL, duration, date), excluding Shorts and livestreams.

- Minimal standalone CLI script (no dependencies)
- Newest-first ordering
- Output: `Title, URL, Length, Date`

## Requirements

- Python 3.9+
- YouTube Data API v3 key (free)

## Get an API key

1. Open Google Cloud Console
2. Create a project
3. Enable **YouTube Data API v3**
4. Create credentials → **API key**
5. Copy the key

## Usage

```bash
python yt_channel_videos.py CHANNEL_URL --key API_KEY --out videos.csv
```

Examples:

```bash
python yt_channel_videos.py https://www.youtube.com/@lexfridman --key YOUR_KEY --out videos.csv
```

Using environment variable instead of `--key`:

```bash
export YOUTUBE_API_KEY="YOUR_KEY"
python yt_channel_videos.py https://www.youtube.com/@lexfridman --out videos.csv
```

## Arguments

| Argument | Required | Default | Description |
|---|---:|---|---|
| `channel_url` | Yes | — | Channel URL (`/channel/<id>` or `/@<handle>`) |
| `--key` | Yes* | `YOUTUBE_API_KEY` | API key |
| `--out` | No | stdout | Output CSV file path |
| `--min-duration` | No | `61` | Minimum duration (seconds). Videos shorter than this are excluded |

\* Required unless `YOUTUBE_API_KEY` is set.

## Output format

CSV columns:

```text
Title,URL,Length,Date
```

Example row:

```text
Deep Learning State of the Art,https://www.youtube.com/watch?v=abc123,1:23:45,2024-10-12
```

## Filtering rules

- **Livestreams** are excluded (items with `liveStreamingDetails`).
- **Shorts** are excluded via a duration threshold (`--min-duration`, default 61 seconds). This is heuristic.

## Supported channel URLs

- `https://www.youtube.com/@handle`
- `https://www.youtube.com/channel/UCxxxx`

## Windows EXE (optional)

Build a Windows executable with PyInstaller **on Windows**:

```bat
python -m pip install --upgrade pip
python -m pip install pyinstaller
pyinstaller --onefile --name ytdump yt_channel_videos.py
```

EXE output:

- `dist\\ytdump.exe`

Run:

```bat
dist\\ytdump.exe https://www.youtube.com/@lexfridman --key YOUR_KEY --out videos.csv
```

## License

MIT
