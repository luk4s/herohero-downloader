#!/usr/bin/env python3
from datetime import datetime
import os
import requests
import sys
import xml.etree.ElementTree as ET

# USAGE: herohero-downloader.py <https://herohero.co/services/functions/rss-feed>

feed_uri = sys.argv[1]
if not feed_uri.startswith("https://herohero.co"):
  raise "HeroHero feed URI required"

response = requests.get(feed_uri)
root_node = ET.fromstring(response.content)

download_dir = root_node.find(".//channel/title").text
if not os.path.exists(download_dir):
  os.mkdir(download_dir)

def download_file(filename, url):
  destination = f"./{download_dir}/{filename}"
  if os.path.exists(destination):
    return

  print(f"Downloading {filename}...")
  response = requests.get(url)
  f = open(destination, 'wb')
  for chunk in response.iter_content(chunk_size=512 * 1024): 
      if chunk: # filter out keep-alive new chunks
          f.write(chunk)
  f.close()

n = 1
items = root_node.findall(".//item")
list.reverse(items)
for item in items:
  id = item.find("guid").text
  pubDate = item.find("pubDate").text
  released_date = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
  url = item.find("enclosure").attrib["url"]
  title = item.find("description").text.splitlines()[0].strip().split(".")[0]
  ext = url.split(".")[-1]
  filename = f"{n:03d} - {title} ({released_date.strftime('%F')}).{ext}"
  download_file(filename, url)
  n += 1