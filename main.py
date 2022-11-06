import os
from urllib.parse import urlparse
import requests
import praw
from PIL import Image
import imagehash


def isImage(url):
    if url.endswith((".png", ".jpeg", ".jpg", ".webp")):
        return True
    else:
        return False


def similarity(post1, post2):
    hash1 = imagehash.average_hash(Image.open(
        f"./cache/{post1.id}{os.path.splitext(urlparse(post1.url).path)[1]}"))
    hash2 = imagehash.average_hash(Image.open(
        f"./cache/{post2.id}{os.path.splitext(urlparse(post2.url).path)[1]}"))
    return 100 - (((hash1 - hash2)/64)*100)


reddit = praw.Reddit("devhumour-bot")
rising = reddit.subreddit("ProgrammerHumor").rising()

for post in rising:
    path = f"./cache/{post.id}{os.path.splitext(urlparse(post.url).path)[1]}"
    if isImage(post.url) and not os.path.exists(path):
        img = requests.get(post.url).content
        with open(path, "wb") as handler:
            handler.write(img)

for post in rising:
    print(post.url)
    if isImage(post.url):
        for otherPost in rising:
          if post.id != otherPost.id:
            print(similarity(post, otherPost))
