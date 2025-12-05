#!/usr/bin/env python3
# USAGE: herohero-downloader.py <https://svc-prod-na.herohero.co/rss-feed/blabla>
from datetime import datetime
import os
import requests
import sys
import xml.etree.ElementTree as ET
import re

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

feed_uri = sys.argv[1]

response = requests.get(feed_uri)
root_node = ET.fromstring(response.content)

download_dir = root_node.find(".//channel/title").text
if not os.path.exists(download_dir):
  os.mkdir(download_dir)

def download_file(filename, url):
  destination = f"./{download_dir}/{filename}"
  if os.path.exists(destination):
    return destination

  response = requests.get(url, stream=True)
  total_size = int(response.headers.get('content-length', 0))
  downloaded = 0

  with open(destination, 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
      if chunk:
        f.write(chunk)
        downloaded += len(chunk)
        percent = int(100 * downloaded / total_size) if total_size > 0 else 0
        sys.stdout.write(f"\r{percent}% downloaded ({downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB)")
        sys.stdout.flush()

  return destination

def meta_atributes(item):
  data = {}
  pubDate = item.find("pubDate").text
  released_date = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
  title = item.find("title").text.strip()

  data["date"] = released_date
  data["title"] = title
  data["description"] = item.find("description").text
  data["guid"] = item.find("guid").text

  return data


items = root_node.findall(".//item")
list.reverse(items)

n = 1
for item in items:
    id = item.find("guid").text
    data = meta_atributes(item)
    data["number"] = n
    url = item.find("enclosure").attrib["url"]
    ext = url.split(".")[-1]

    raw_filename = f"{data['date'].strftime('%F')} {n:03d} - {data['title']}.{ext}"
    filename = sanitize_filename(raw_filename)

    file = download_file(filename, url)

    n += 1
