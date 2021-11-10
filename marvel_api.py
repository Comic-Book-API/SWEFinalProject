import flask
import os
from dotenv import find_dotenv, load_dotenv
import requests
import base64
import hashlib
import time

# https://stackoverflow.com/questions/53356636/invalid-hash-timestamp-and-key-combination-in-marvel-api-call helped me get the api calls to work

load_dotenv(find_dotenv())

public_key = os.getenv("marvel_public_key")
private_key = os.getenv("marvel_private_key")

hash = hashlib.md5()


# The Marvel API requires servers to have parameters before accessing them. The paramaters are: a timestamp (ts), the public api key, and a hash with the md5 algorithm of the ts, public key, and private key mashed together
# To do this, I made ts a random time, converted ts, public key, and private key into byte format so they can be fed into the md5 formatter, and then convert the hashed string into the hex form, which is the form required by the Marvel API.
ts = str(time.time())
ts_byte = bytes(ts, "utf-8")
public_byte = bytes(public_key, "utf-8")
private_byte = bytes(private_key, "utf-8")
hash.update(ts_byte)
hash.update(private_byte)
hash.update(public_byte)
hashhex = hash.hexdigest()

urlAddOn = f"?ts={ts}&apikey={public_key}&hash={hashhex}"
search = input("Enter in the name of a comic book: ")


def getComicByTitle(search, offset):
    base_url = "https://gateway.marvel.com/v1/public/comics"
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        "titleStartsWith": search,
        "limit": 1,
        "offset": offset,
    }

    endpoint_request = requests.get(url=base_url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]

    # Returns the title, the on sale date of the comic, a link to an image of the comic, and a list of collaborators who worked on the comic.
    title = data_results[0]["title"]
    onSaleDate = data_results[0]["dates"][0]["date"]
    creators = data_results[0]["creators"]["items"]
    creatorList = []

    # For the API, we have to change the link returned by the json or else it gives a permission denied error. To do this, we just append a string onto the end that Marvel has pre-defined. standard_fantastic is the version of the img we chose.
    imgPath = data_results[0]["images"][0]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"

    for i in range(len(creators)):
        creatorList.append(data_results[0]["creators"]["items"][i]["name"])

    print(data_results[0].keys())

    return (title, creatorList, onSaleDate, imgLink)


def getComicByCharacter(search, offset):
    # Because the parameter must be a character ID, we have to make a call to the getCharacters so we can have the ID of the search query. From there, it's passed into the parameters to perform the search.
    (id, name, description, imgLink) = getCharacter(search, 0)
    base_url = "https://gateway.marvel.com/v1/public/comics"
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        "characters": id,
        "limit": 1,
        "offset": offset,
    }
    endpoint_request = requests.get(url=base_url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]

    title = data_results[0]["title"]

    return getComicByTitle(title, offset)


def getComicByCreator(search, offset):
    creator = getCreatorID(search)
    base_url = "https://gateway.marvel.com/v1/public/comics"
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        "limit": 1,
        "offset": offset,
        "creators": creator,
    }
    endpoint_request = requests.get(url=base_url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]

    title = data_results[0]["title"]

    return getComicByTitle(title, offset)


def getSeries(search, offset):
    base_url = "https://gateway.marvel.com/v1/public/series"
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        "titleStartsWith": search,
        "limit": 1,
    }

    endpoint_request = requests.get(url=base_url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]
    next = data_results[0]["next"]
    titleList = []
    for i in range(len(data_results)):
        titleList.append(data_results[i]["title"])
    print(titleList, next)


def getCharacter(search, offset):
    base_url = "https://gateway.marvel.com/v1/public/characters"
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        "nameStartsWith": search,
        "limit": 1,
        "offset": offset,
    }
    endpoint_request = requests.get(url=base_url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]

    name = data_results[0]["name"]
    description = data_results[0]["description"]
    id = data_results[0]["id"]

    imgPath = data_results[0]["thumbnail"]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"

    return (id, name, description, imgLink)


# Helper function to fetch the id of a creator to feed into the getComicByCreator function.
def getCreatorID(search):
    base_url = "https://gateway.marvel.com/v1/public/creators"
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        "nameStartsWith": search,
        "limit": 1,
    }

    endpoint_request = requests.get(url=base_url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]

    return data_results[0]["id"]


print(getComicByTitle(search, 0))
