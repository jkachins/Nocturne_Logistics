import csv
import redis
from urllib.parse import urlparse
import json
import os

url = urlparse(os.environ.get('REDISCLOUD_URL'))
r = redis.Redis(host=url.hostname, port=url.port, password=url.password)

def read_file():
    with open("Skills.csv", "r") as f:
        reader = csv.DictReader(f)
        contents = list(reader)
    
    l = [ process_row(r) for r in contents ]
    m = {}
    for row in l:
        m.setdefault(row["skill_list"], []).append(row)
    for k,v in m.items():
        r.set("LIST: " + k, json.dumps(v))


def process_row(r):
    d = {}
    d["name"] = r["Skill name"]
    d["skill_list"] = r["List"]
    d["cost"] = r["Cost"]
    d["build"] = r["Build"]
    return d

if __name__ == '__main__':
    read_file()
