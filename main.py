import sqlite3
from io import BytesIO
import urllib.request as request

import imagehash
import praw
from PIL import Image

conn = sqlite3.connect("database.sqlite")

cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS posts (id VARCHAR(10) UNIQUE NOT NULL, image BLOB NOT NULL);")


def isImage(url):
    if url.endswith((".png", ".jpeg", ".jpg", ".webp")):
        return True
    else:
        return False


def similarity(img1, img2):
    print(img1.size, img2.size)
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
            print(similarity(img, dbimg))

        cursor.execute("INSERT INTO posts VALUES (?, ?);",
                       (post.id, bytearray(imgdata)))


conn.commit()
