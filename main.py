import sqlite3
from io import BytesIO
import urllib.request as request
# import threading

from imagehash import average_hash
import praw
from PIL import Image
from datetime import datetime


def isImage(url):
    return url.endswith((".png", ".jpeg", ".jpg", ".webp"))


def similarity(img1, img2):
    hash1 = average_hash(img1)
    hash2 = average_hash(img2)
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


def checkPosts(list):
    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS posts (id VARCHAR(10) UNIQUE NOT NULL, image BLOB NOT NULL, created_utc VARCHAR(20) NOT NULL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS reposts (original_id VARCHAR(10), copy_id VARCHAR(10))")
    
    for post in list:
        dbposts = cursor.execute("SELECT * FROM posts;").fetchall()
        if isImage(post.url) and not findPostInDatabasePosts(post, dbposts):
            print(f"Processing '{post.id}'")
            imgdata = getImgFromURL(post.url)
            img = Image.open(BytesIO(imgdata))

            for dbpost in dbposts:
                dbimg = Image.open(BytesIO(dbpost[1]))
                sim = similarity(img, dbimg)
                if (sim > 99):
                    post_created_at = datetime.fromtimestamp(post.created_utc)
                    dbpost_created_at = datetime.fromtimestamp(float(dbpost[2]))

                    og = post.id if post_created_at < dbpost_created_at else dbpost[0]
                    copy = post.id if post_created_at > dbpost_created_at else dbpost[0]

                    print(f"{sim}: og: {og}, copy: {copy}")
                    cursor.execute(
                        "INSERT INTO reposts VALUES (?, ?);", (og, copy))

            cursor.execute("INSERT INTO posts VALUES (?, ?, ?);",
                           (post.id, bytearray(imgdata), post.created_utc))

    conn.commit()


if __name__ == "__main__":
    reddit = praw.Reddit("devhumour-bot")
    subreddit = reddit.subreddit("ProgrammerHumor")
    
    rising = [_ for _ in subreddit.rising(limit=None)]
    checkPosts(rising)
    
    # TODO: create threads for different sorting types
    # rising = [_ for _ in subreddit.rising(limit=None)]
    # hot = [_ for _ in subreddit.hot(limit=None)]
    # top_all = [_ for _ in subreddit.top(limit=None, time_filter="all")]
    # new = [_ for _ in subreddit.new(limit=None)]
    
    # print('got posts')
    
    # rising_thread = threading.Thread(target=checkPosts,args=([rising]))
    # hot_thread = threading.Thread(target=checkPosts, args=([hot]))
    # top_all_thread = threading.Thread(target=checkPosts, args=([top_all]))
    # new_thread = threading.Thread(target=checkPosts, args=([new]))
    
    # rising_thread.start()
    # hot_thread.start()
    # top_all_thread.start()
    # new_thread.start()
    
    # rising_thread.join()
    # hot_thread.join()
    # top_all_thread.join()
    # new_thread.join()
    