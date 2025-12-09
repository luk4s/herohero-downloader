#!/usr/bin/env python3
"""
Usage:
    herohero-downloader.py <rss_feed_url>

Requirements:
    pip install aiohttp tqdm
"""

import aiohttp
import asyncio
import json
import os
import re
import sys

from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import xml.etree.ElementTree as ET


# Cache files
CACHE_FILE = Path("feed.xml")
META_FILE = Path("feed.metadata.json")

# Place to save downloads
ROOT_DOWNLOAD_FOLDER = "downloads"

# Limit of parallel downloads
try:
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
except ValueError:
    MAX_CONCURRENT_DOWNLOADS = 3
    print("Warning: MAX_CONCURRENT_DOWNLOADS must be a valid integer, using default: 3", file=sys.stderr)


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def load_meta():
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_meta(meta: dict):
    META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")


async def fetch_rss_with_cache_validation(url: str) -> str:
    """
    Fetch RSS feed using ETag / Last-Modified validation.
    Returns cached version if server responds 304 Not Modified.
    """

    headers = {}
    meta = load_meta()

    if "etag" in meta:
        headers["If-None-Match"] = meta["etag"]
    if "last_modified" in meta:
        headers["If-Modified-Since"] = meta["last_modified"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:

            if resp.status == 304:
                print("RSS not modified → using cached feed.xml")
                return CACHE_FILE.read_text(encoding="utf-8")

            resp.raise_for_status()
            text = await resp.text()

            # Save feed
            CACHE_FILE.write_text(text, encoding="utf-8")
            print("RSS updated → feed.xml")

            # Save metadata
            new_meta = {}
            if "ETag" in resp.headers:
                new_meta["etag"] = resp.headers["ETag"]
            if "Last-Modified" in resp.headers:
                new_meta["last_modified"] = resp.headers["Last-Modified"]

            save_meta(new_meta)
            print("Metadata saved → feed.metadata.json")

            return text


async def download_file(session, url: str, target_path: Path):
    """Download a file asynchronously with tqdm progress bar."""

    if target_path.exists():
        print(f"[SKIP] {target_path.name}")
        return target_path

    async with session.get(url) as resp:
        resp.raise_for_status()

        total_size = int(resp.headers.get("content-length", 0))

        # tqdm progress bar
        progress = tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=target_path.name,
            leave=True,
        )

        with target_path.open("wb") as f:
            async for chunk in resp.content.iter_chunked(1024 * 1024):
                f.write(chunk)
                progress.update(len(chunk))

        progress.close()

    return target_path


async def limited_download(semaphore, session, url, target_path):
    """Ensure only MAX_CONCURRENT_DOWNLOADS run at once."""
    async with semaphore:
        return await download_file(session, url, target_path)


def parse_item_metadata(item):
    pub_date = item.findtext("pubDate")
    released_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")

    return {
        "date": released_date,
        "title": item.findtext("title", "").strip(),
        "description": item.findtext("description", ""),
        "guid": item.findtext("guid", ""),
    }


async def main():
    if len(sys.argv) < 2:
        print("Usage: herohero-downloader.py <rss_feed_url>")
        sys.exit(1)

    feed_url = sys.argv[1]

    # Load or update RSS feed
    rss_xml = await fetch_rss_with_cache_validation(feed_url)

    root = ET.fromstring(rss_xml)

    title = root.findtext(".//channel/title")
    download_dir = Path(ROOT_DOWNLOAD_FOLDER) / sanitize_filename(title)
    download_dir.mkdir(exist_ok=True, parents=True)

    items = root.findall(".//item")
    items.reverse()  # earliest first

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, item in enumerate(items, start=1):
            meta = parse_item_metadata(item)

            enclosure = item.find("enclosure")
            url = enclosure.attrib["url"]
            ext = url.split(".")[-1]

            raw = f"{meta['date'].strftime('%F')} {idx:03d} - {meta['title']}.{ext}"
            filename = sanitize_filename(raw)
            target = download_dir / filename

            tasks.append(limited_download(semaphore, session, url, target))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
