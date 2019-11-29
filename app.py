# app.py
from flask import Flask, request, jsonify
import os
import redis
from urllib.parse import urlparse
import pandas_access as mdb

app = Flask(__name__)
url = urlparse(os.environ.get('REDISCLOUD_URL'))
file_cache = redis.Redis(host=url.hostname, port=url.port, password=url.password)

@app.route('/getmsg/', methods=['GET'])
def respond():
	
    if not os.path.exists("Character.accdb"):
        file_binary = file_cache.get("db")
        #with open('Character.accdb', 'wb') as f:
        #    f.write(file_binary)
        newf = open("Character.accdb", "wb")
        newf.write(file_binary)
        newf.close()

    query = '`Character Number` == %s'

    # Retrieve the name from url parameter
    idn = request.args.get("id", None)

    response = {}

    # Check if user sent a name at all
    if not idn:
        response["ERROR"] = "no id found, please send id."
    # Check if the user entered a number not a name
    elif not str(idn).isdigit():
        response["ERROR"] = "name must be numeric."
    else:
        df = mdb.read_table("Character.accdb", "Characters")
        character = df.query(query%idn)
        if character.empty:
            response["ERROR"] = "No character for id %s"%idn
        else:
            response["name"] = character['Character Name'].values[0]
            response["id"] = idn

    # Return the response in json format
    return jsonify(response)

@app.route('/post/', methods=['POST'])
def post_something():
    param = request.form.get('name')
    print(param)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    if param:
        return jsonify({
            "Message": f"Welcome {name} to our awesome platform!!",
            # Add this option to distinct the POST request
            "METHOD" : "POST"
        })
    else:
        return jsonify({
            "ERROR": "no name found, please send a name."
        })

# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)

