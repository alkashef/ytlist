# ytlist (YouTube Channel CSV Exporter)

Export all regular videos from a YouTube channel to CSV (title, URL, duration, date), excluding Shorts and livestreams.

- Simple CLI script with minimal dependencies
- Newest-first ordering
- Output: `Title, URL, Length, Date`

## Requirements

- Python 3.9+
- YouTube Data API v3 key
- `python-dotenv` (for configuration management) 

## Setup

### 1. Install dependencies

```bash
pip install python-dotenv
```

### 2. Configure API key

Create a `config/.env` file in the project directory with your YouTube API key:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
DEFAULT_CHANNEL=https://www.youtube.com/@NateBJones
```

⚠️ **IMPORTANT**: The `config/.env` file is listed in `.gitignore` and should **never** be committed to version control. It contains sensitive credentials.

## Usage

Once configured, simply run:

```bash
python ytlist.py --out videos.csv
```

This uses the default channel from `config/.env`. 

To use a different channel:

```bash
python ytlist.py https://www.youtube.com/@lexfridman --out videos.csv
```

## Alternative: Pass API key via command line

```bash
python ytlist.py CHANNEL_URL --key YOUR_API_KEY --out videos.csv
```

## Alternative: Use environment variable

```bash
export YOUTUBE_API_KEY="YOUR_KEY"
python ytlist.py CHANNEL_URL --out videos.csv
```

## Arguments

| Argument | Required | Default | Description |
|---|---:|---|---|
| `channel_url` | No | `DEFAULT_CHANNEL` | Channel URL (`/channel/<id>` or `/@<handle>`) |
| `--key` | Yes* | `YOUTUBE_API_KEY` | API key |
| `--out` | No | stdout | Output CSV file path |
| `--min-duration` | No | `61` | Minimum duration (seconds). Videos shorter than this are excluded |

\* Required unless `YOUTUBE_API_KEY` is set in `config/.env`.

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
