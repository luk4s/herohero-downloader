#!/usr/bin/env python3
from datetime import datetime
import os
import requests
import sys
import xml.etree.ElementTree as ET
from mutagen.mp4 import MP4

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

  return destination

def write_metadata(filename, data):
  tags = MP4(filename).tags
  tags['\xa9ART'] = data["artist"]
  tags['\xa9alb'] = data["album"]
  tags['desc'] = data["description"]
  tags['\xa9nam'] = data["title"]
  tags['trkn'] = [(data["number"], data["tracks"])]
  tags['purl'] = data["link"]
  tags['egid'] = data["guid"]
  tags['pcst'] = True # Podcast = True
  tags.save(filename)
  return filename

def meta_atributes(item):
  data = {}
  pubDate = item.find("pubDate").text
  released_date = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
  title = item.find("description").text.splitlines()[0].strip().split(".")[0]

  data["date"] = released_date
  data["title"] = title
  data["description"] = item.find("description").text
  data["guid"] = item.find("guid").text

  return data


items = root_node.findall(".//item")
list.reverse(items)
general_metadata = { 
  "tracks": len(items), 
  "album": download_dir, 
  "artist": "Bára",  # TODO: 
  "link": root_node.find(".//link").text
  }
n = 1
for item in items:
  id = item.find("guid").text
  data = meta_atributes(item)
  data["number"] = n
  url = item.find("enclosure").attrib["url"]
  ext = url.split(".")[-1]
  filename = f"{data['date'].strftime('%F')} {n:03d} - {data['title']}.{ext}"
  file = download_file(filename, url)
  if file:
    write_metadata(file, data | general_metadata)
  n += 1