import os
from urllib.parse import urlparse
import requests
import praw
from PIL import Image
import imagehash
import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS posts (id VARCHAR(10) NOT NULL, image BLOB NOT NULL);")


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
rising_iter = reddit.subreddit("ProgrammerHumor").rising(limit=None)
rising = [_ for _ in rising_iter]

for post in rising:
    path = f"./cache/{post.id}{os.path.splitext(urlparse(post.url).path)[1]}"
    if isImage(post.url) and not os.path.exists(path):
        img = requests.get(post.url).content
        print(img)
        cursor.execute("INSERT INTO posts VALUES (?, ?);", (post.id, img))
