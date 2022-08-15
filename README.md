# herohero-downloader
I want play my favorite podcast more comfortably. So this script can download content from herohero.co via feed link.

## Usage
As a subscriber of herohero.co generate feed link.
Then use URL of feed as an argument of script:
```bash
./herohero-downloader.py https://herohero.co/services/functions/rss-feed?token=blabla
```

Script download XML feed, based on title of user show create folder in folder you run it and download it...
As a `filename` is used first line of description (until .) with #N of post and date of published.

If same filename already exist, skip this post = so if you set cronjob, you can easily download every new "episode".

