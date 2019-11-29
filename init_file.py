import os
import redis
from urllib.parse import urlparse
import pandas_access as mdb

url = urlparse(os.environ.get('REDISCLOUD_URL'))
file_cache = redis.Redis(host=url.hostname, port=url.port, password=url.password)

if not os.path.exists("Character.accdb"):
    file_binary = file_cache.get("db")
    newf = open("Character.accdb", "wb")
    newf.write(file_binary)
    newf.close()
