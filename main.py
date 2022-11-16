import sqlite3
from io import BytesIO
import urllib.request as request

import imagehash
import praw
from PIL import Image
from datetime import datetime

conn = sqlite3.connect("database.sqlite")

cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS posts (id VARCHAR(10) UNIQUE NOT NULL, image BLOB NOT NULL, image_url VARCHAR(40) NOT NULL, posted_at TIMESTAMP NOT NULL);")
cursor.execute("CREATE TABLE IF NOT EXISTS reposts (original_id VARCHAR(10), copy_id VARCHAR(10))")


def isImage(url):
    if url.endswith((".png", ".jpeg", ".jpg", ".webp")):
        return True
    else:
        return False


def similarity(img1, img2):
    hash1 = imagehash.average_hash(img1)
    hash2 = imagehash.average_hash(img2)
    return 100 - (((hash1 - hash2)/64)*100)


def findPostInDatabasePosts(post, list):
    for item in list:
        if item[0] == post.id:
            return True

    return False


def getImgFromURL(url):
    file = request.urlopen(url)
    data = file.read()

    return data


reddit = praw.Reddit("devhumour-bot")
rising_iter = reddit.subreddit("ProgrammerHumor").rising(limit=None)
rising = [_ for _ in rising_iter]

for post in rising:
    dbposts = cursor.execute("SELECT * FROM posts;").fetchall()
    print(f"\n\nProcessing '{post.id}'")
    if isImage(post.url) and not findPostInDatabasePosts(post, dbposts):
        imgdata = getImgFromURL(post.url)
        img = Image.open(BytesIO(imgdata))

        for dbpost in dbposts:
            dbimg = Image.open(BytesIO(dbpost[1]))
            sim = similarity(img, dbimg)
            if (sim > 95):
                post_created_at = datetime.fromtimestamp(post.created_utc)
                dbpost_created_at = datetime.fromtimestamp(dbpost.created_utc)

                og = post if post_created_at < dbpost_created_at else dbpost
                copy = post if post_created_at > dbpost_created_at else dbpost

                print(f"{sim}: og: {og.url}, copy: {copy.url}")
                cursor.execute("INSERT INTO reposts VALUES (?, ?);", (og.id, copy.id))

        cursor.execute("INSERT INTO posts VALUES (?, ?);", (post.id, bytearray(imgdata)))


conn.commit()
