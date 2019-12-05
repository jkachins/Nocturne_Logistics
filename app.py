# app.py
from flask import Flask, request, jsonify
import os
import redis
from urllib.parse import urlparse
import pandas_access as mdb
import csv

app = Flask(__name__)
app.debug = True
url = urlparse(os.environ.get('REDISCLOUD_URL'))
file_cache = redis.Redis(host=url.hostname, port=url.port, password=url.password)

def refresh_access_db():
    if not os.path.exists("Character.accdb"):
        file_binary = file_cache.get("db")
        newf = open("Character.accdb", "wb")
        newf.write(file_binary)
        newf.close()

        
#TODO (kachinsk): Have this use standard "with open() as f" syntax
def refresh_csv_db():
    if not os.path.exists("Character.csv"):
        csv_contents = file_cache.get("csv")
        newf = open("Character.csv", 'wb')
        newf.write(csv_contents)
        newf.close()


#TODO (kachinsk): Unify Character behind interface
def get_character_from_access(idn):
    query = '`Character Number` == %s'
    df = mdb.read_table("Character.accdb", "Characters")
    character = df.query(query%idn)
    if character.empty:
        return None
    return character
        

def get_character_from_csv(idn):
    with open('Character.csv') as f:
        reader = csv.DictReader(f)
        my_row = [row for row in reader if row['Character Number'] == idn]
        if my_row:
            return my_row[0]
        return None


def clean_character_dict(character):
    skill_list = [v for (k,v) in character.items() if v and k.startswith('Skill name')]
    character['Skill List'] = skill_list 
    year_stuff(character)
    return {k:v for (k,v) in character.items() if v and not k.startswith('Skill name')}


#TODO (kachinsk): Consolidate the stuff functions into one so we don't have to iterate
#over the character dictionary repeatedly
def genetic_stuff(character):
    genetic_keys = ["PowerB", "PowerO", "VigorB", "VigorO", "MannaB", "MannaB", "EssenceB", "EssenceO"]
    for k in genetic_keys:
        pass

def year_stuff(character):
    if not character["Date Created"]:
        return
    build_bought = {}
    to_delete = []
    year_created = int(character["Date Created"].split(" ")[1])
    for (k,v) in character.items(): 
        if not k.startswith("Build Buy"):
            continue
        can_buy_year = k[-4:].isdigit() and int(k[-4:]) >= year_created
        if can_buy_year:
            build_bought[k] = v
        to_delete.append(k)
    for key in to_delete:
        del character[key] 
    character["Year Build"] = build_bought
    

@app.route('/getmsg/', methods=['GET'])
def respond():
    #Ensure that DB file exists
    #refresh_access_db()
    refresh_csv_db()

    response = {}

    #TODO (kachinsk): This is all a bit of ugly for now.
    #We should remove the id field eventually and only allow through FID
    idn = request.args.get("id", None)
    fidn = request.args.get("fid", None)
    if fidn:
        idn = file_cache.hget("ForumToUser", fidn) 
        if idn:
            idn = str(int(idn))
        else:
            response["ERROR"] = "No Forum ID found"
            return jsonify(response)

    if not idn:
        response["ERROR"] = "no id found, please send id."
    elif not str(idn).isdigit():
        response["ERROR"] = "name must be numeric."
    else:
        character = get_character_from_csv(idn)
        if character:
            response["name"] = character['Character Name']
            response["FULL"] = clean_character_dict(character)
            response["id"] = idn
        else:
            response["ERROR"] = "No character for id %s"%idn        

    return jsonify(response)

@app.route('/post/', methods=['POST'])
def post_something():
    param = request.form.get('name')
    if param:
        return jsonify({
            "Message": f"Welcome {name} to our awesome platform!!",
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
    app.run(debug=True, threaded=True, port=5000)

