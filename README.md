# herohero-downloader
Download podcast content from herohero.co via RSS feed link.

## Usage

### Docker (Recommended)
```bash
docker run -v $(pwd)/downloads:/app/downloads ghcr.io/luk4s/herohero-downloader:latest "https://herohero.co/services/functions/rss-feed?token=YOUR_TOKEN"
```

### Local Python
```bash
pip install -r requirements.txt
./herohero-downloader.py "https://herohero.co/services/functions/rss-feed?token=YOUR_TOKEN"
```

## Environment Variables

- `MAX_CONCURRENT_DOWNLOADS` - Controls how many parallel download streams are allowed (default: 3)
  ```bash
  docker run -e MAX_CONCURRENT_DOWNLOADS=5 -v $(pwd)/downloads:/app/downloads ghcr.io/luk4s/herohero-downloader:latest "https://herohero.co/services/functions/rss-feed?token=YOUR_TOKEN"
  ```

## How it works
- Downloads XML feed and creates folder based on show title
- Uses first line of description + post number + date as filename
- Skips existing files (safe for cronjobs)
