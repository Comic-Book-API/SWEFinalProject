import flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import find_dotenv, load_dotenv


app = flask.Flask(__name__)

load_dotenv(find_dotenv())

# database location
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://tmp.db"
# Database config and setup
db = SQLAlchemy(app)
MAX_ID_ENTRIES = 20 # If this value is made greater, the database must be completely reinitialized

# TODO:
# password cryptography
# function to make a new user
# string id encoding
class Account(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.BigInteger, nullable=False)
    # The following fields encode a list of up to 20 id's into a string.
    # This code assumes that the max length for any one of these ids is 8 digits/characters
    # the encoding for this is very simple. each item is separated by ;'s
    # for example, "1234;5351;1234;413234;41234124"
    comics = db.Column(db.String(200))
    characters = db.Column(db.String(200))

db.create_all()
db.session.commit()

# removes comic from the comics entry for the given user
# returns 0 if successful, -1 if the comic could not be found
def remove_comic(uid, comic_id):
    comics = decode_string(get_account_db_comics(uid))
    if comics.count(comic_id) == 0:
        return -1
    comics.remove(comic_id)
    get_account_db_entry(uid).comics = encode_string(comics)
    db.session.commit()
    return 0

# removes character from the characters entry for the given user
# returns 0 if successful, -1 if the entry could not be found
def remove_character(uid, character_id):
    characters = decode_string(get_account_db_characters(uid))
    if characters.count(character_id) == 0:
        return -1
    characters.remove(character_id)
    get_account_db_entry(uid).characters = encode_string(characters)
    db.session.commit()
    return 0

# adds comic from the comics entry for the given user
# returns 0 if successful, -1 if the entry could not be added because the max has been reached, and -2 if the entry is already present
def add_comic(uid, comic_id):
    comics = decode_string(get_account_db_comics(uid))
    if len(comics) >= 20:
        return -1
    if comics.count(comic_id) > 0:
        return -2
    comics.append(comic_id)
    get_account_db_entry(uid).comics = encode_string(comics)
    db.session.commit()
    return 0

# adds character from the character entry for the given user
# returns 0 if successful, -1 if the entry could not be added because the max has been reached, and -2 if the entry is already present
def add_character(uid, character_id):
    characters = decode_string(get_account_db_characters(uid))
    if len(characters) >= 20:
        return -1
    if characters.count(character_id) > 0:
        return -2
    characters.append(character_id)
    get_account_db_entry(uid).characters = encode_string(characters)
    db.session.commit()
    return 0

# decodes a string, returning the encoded list of ids
# return value of None means that the encoded string is invalid somehow
def decode_string(encoded_string):
    id_list = encoded_string.split(";")
    # verification tests:
    for id in id_list:
        # no id should be empty
        if len(id) == 0:
            return None
        # all chars should be numbers
        if not id.isdecimal():
            return None
    return id_list

# returns the character at the given index
def get_character(uid, character_index):
    characters = decode_string(get_accound_db_characters(uid))
    return characters[character_index]

# returns the comci at the given index
def get_comic(uid, comic_index):
    comics = decode_string(get_account_db_comics(uid))
    return comics[comic_index]

def encode_string(id_list):
    ids_str = ""
    for id in id_list:
        if len(ids_str) != 0:
            ids_str += ";"
        ids_str += id
    return ids_str

def get_account_db_entry(uid):
    acc = Account.query.filter_by(uid=uid)
    return acc
def get_account_db_comics(uid):
    return get_account_db_entry(uid).comics
def get_accound_db_characters(uid):
    return get_account_db_entry(uid).characters

@app.route("/")
def index():
    return flask.render_template("index.html") #signup.html


app.run()
