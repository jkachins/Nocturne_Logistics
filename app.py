# app.py
from flask import Flask, request, jsonify, Response
import os
import redis
from urllib.parse import urlparse
import pandas_access as mdb
import csv
import json
from skill import Skill


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
    c = character.copy()
    skill_stuff(c)
    build_stuff(c)
    genetic_stuff(c)
    player_stuff(c)
    return c


def add_to_character_library(library, list_name, n):
    l = file_cache.get("LIST: " + list_name)
    if not l:
        return
    skills = json.loads(l)
    for skill in skills:
        s = Skill.from_dict(skill)
        library[s.get_name(n)] = list_name
        

#TODO (kachinsk): Consolidate the stuff functions into one so we don't have to iterate
#over the character dictionary repeatedly
def skill_stuff(character):
    skill_library = file_cache.hgetall("Skills") 
    delete_keys = [k for (k,v) in character.items() if k.startswith("Skill name")]
    character_skills = [v for (k,v) in character.items() if v and k.startswith('Skill name')]
    character_skill_map = {}
    character_skill_library= {}

    for n in range(1, 6):
        profession = "Profession" + str(n)
        if not character[profession]:
            break
        add_to_character_library(character_skill_library, character[profession], n)
    if character["Advanced1"]:
        add_to_character_library(character_skill_library, character["Advanced1"], 1)
    add_to_character_library(character_skill_library, "Common", 1)
    add_to_character_library(character_skill_library, character["Race"], 1) 
    
    for skill in character_skills:
        character_skill_map.setdefault(character_skill_library.get(skill.strip(), "Unknown"), []).append(skill)
    character["Skills"] = character_skill_map

    for k in delete_keys:
        del character[k]


def genetic_stuff(character):
    genetic_keys = ["PowerB", "PowerO", "VigorB", "VigorO", "MannaB", "MannaO", "EssenceB", "EssenceO"]
    genetics = {}
    for k in genetic_keys:
        if k[-1:] == 'B':
            new_key = k[:-1] + " Bought"
        elif k[-1:] == 'O':
            new_key = "Total " + k[:-1]
        genetics[new_key] = character[k]
        del character[k]
    character["Genetics"] = genetics

def player_stuff(character):
    player_keys = ["Medical Information", "E-mail Address", "Emergency Contact", "Player Name"]
    player = {}
    _move_keys(player_keys, character, player)
    character["Player Info"] = player

def build_stuff(character):
    if not character["Date Created"]:
        return
    build_bought = {}
    year_build = {}
    to_delete = []
    year_created = int(character["Date Created"].split(" ")[1])
    for (k,v) in character.items(): 
        if not k.startswith("Build Buy"):
            continue
        can_buy_year = k[-4:].isdigit() and int(k[-4:]) >= year_created
        if can_buy_year:
            year_build[k] = v
        to_delete.append(k)
    for key in to_delete:
        del character[key]
    extra_keys = ["Build Spent", "10 Year Anniversary", "Build Bought", "Service Build", "Total Build", \
            "Unspent Build", "Camp Cleanup 1", "Camp Cleanup 2", "Camp Cleanup 3"]
    _move_keys(extra_keys, character, build_bought)
    character["Build Info"] = build_bought
    
def _move_keys(keys, origin, dest):
    for k in keys:
        if k in origin:
            dest[k] = origin[k]
            del origin[k]

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

    #return Response(json.dumps(response), 
    #        mimetype='application/json',
    #        headers={'Content-Disposition':'attachment;filename=character.json'})
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

