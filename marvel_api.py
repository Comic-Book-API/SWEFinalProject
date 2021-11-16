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


def getJSONData(searchField, url, search, offset):
    params = {
        "ts": ts,
        "apikey": public_key,
        "hash": hashhex,
        f"{searchField}": search,
        "limit": 1,
        "offset": offset,
    }
    endpoint_request = requests.get(url=url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]
    return data_results


def getComicByTitle(search, offset):
    data_results = getJSONData(
        "titleStartsWith", "https://gateway.marvel.com/v1/public/comics", search, offset
    )

    # Catch out of bounds error
    if len(data_results) == 0:
        return False
    # Returns the title, the on sale date of the comic, a link to an image of the comic, and a list of collaborators who worked on the comic.
    title = data_results[0]["title"]
    onSaleDate = data_results[0]["dates"][0]["date"]
    creators = data_results[0]["creators"]["items"]
    creatorList = []

    # For the API, we have to change the link returned by the json or else it gives a permission denied error. To do this, we just append a string onto the end that Marvel has pre-defined. standard_fantastic is the version of the img we chose.
    imgPath = data_results[0]["thumbnail"]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"

    for i in range(len(creators)):
        creatorList.append(data_results[0]["creators"]["items"][i]["name"])

    returnArray = []
    returnArray.append(title)
    returnArray.append(onSaleDate)
    return (title, creatorList, onSaleDate, imgLink)


def getComicByCharacter(search, offset):
    # Because the parameter must be a character ID, we have to make a call to the getCharacters so we can have the ID of the search query. From there, it's passed into the parameters to perform the search.
    (id, name, description, imgLink) = getCharacter(search, 0)
    data_results = getJSONData(
        "characters", "https://gateway.marvel.com/v1/public/comics", id, offset
    )

    title = data_results[0]["title"]

    return getComicByTitle(title, offset)


def getComicByCreator(search, offset):
    # We can't search for the creator by name. It has to be by ID, so we need to call the helper function that will return the creator id of the search query/
    creator = getCreatorID(search)
    data_results = getJSONData(
        "creators", "https://gateway.marvel.com/v1/public/comics", creator, offset
    )

    title = data_results[0]["title"]

    return getComicByTitle(title, offset)


def getSeries(search, offset):
    # Not sure what we're going to do with this yet, but it doesn't hurt to includ0e it.
    data_results = getJSONData(
        "titleStartsWith", "https://gateway.marvel.com/v1/public/series", search, offset
    )
    titleList = []
    for i in range(len(data_results)):
        titleList.append(data_results[i]["title"])

    return titleList


def getCharacter(search, offset):
    data_results = getJSONData(
        "nameStartsWith",
        "https://gateway.marvel.com/v1/public/characters",
        search,
        offset,
    )
    if len(data_results) == 0:
        return False
    name = data_results[0]["name"]
    description = data_results[0]["description"]
    id = data_results[0]["id"]

    imgPath = data_results[0]["thumbnail"]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"

    return (id, name, description, imgLink)


# Helper function to fetch the id of a creator to feed into the getComicByCreator function.
def getCreatorID(search):
    data_results = getJSONData(
        "nameStartsWith", "https://gateway.marvel.com/v1/public/creators", search
    )
    return data_results[0]["id"]
