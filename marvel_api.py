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

hash = (
    hashlib.md5()
)  # w5 algorithm of the ts, public key, and private key mashed together
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
    if searchField == "nameStartsWith":
        limit = 100
        params = {
            "ts": ts,
            "apikey": public_key,
            "hash": hashhex,
            f"{searchField}": search,
            "limit": limit,
            "offset": offset,
        }
    else:
        limit = 10
        params = {
            "ts": ts,
            "apikey": public_key,
            "hash": hashhex,
            f"{searchField}": search,
            "limit": limit,
            "offset": offset,
            "noVariants": True,
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
    imgUnavailable = "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    title = []
    onSaleDate = []
    creatorList = []
    buyLink = []
    img = []
    creatorArr = []

    # For the API, we have to change the link returned by the json or else it gives a permission denied error. To do this, we just append a string onto the end that Marvel has pre-defined. standard_fantastic is the version of the img we chose.
    imgPath = data_results[0]["thumbnail"]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"

    if len(data_results) >= 10:
        for i in range(10):
            creatorList = []
            title.append(data_results[i]["title"])
            onSaleDate.append(data_results[i]["dates"][0]["date"])
            buyLink.append(data_results[i]["urls"][0]["url"])
            imgPath = data_results[i]["thumbnail"]["path"]
            imgLink = imgPath + "/standard_fantastic.jpg"
            if imgLink == imgUnavailable:
                img.append("/static/comic error message.png")
            else:
                img.append(imgLink)
            creators = data_results[i]["creators"]["items"]
            for j in range(len(creators)):
                creatorList.append(data_results[i]["creators"]["items"][j]["name"])
            creatorArr.append(creatorList)

    else:
        for i in range(len(data_results)):
            title.append(data_results[i]["title"])
            onSaleDate.append(data_results[i]["dates"][0]["date"])
            buyLink.append(data_results[i]["urls"][0]["url"])
            imgPath = data_results[i]["thumbnail"]["path"]
            imgLink = imgPath + "/standard_fantastic.jpg"
            img.append(imgLink)
            creators = data_results[i]["creators"]["items"]
            for j in range(len(creators)):
                creatorList.append(data_results[i]["creators"]["items"][j]["name"])
            creatorArr.append(creatorList)
    return (title, creatorArr, onSaleDate, img, buyLink)


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
    imgUnavailable = "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    data_results = getJSONData(
        "nameStartsWith",
        "https://gateway.marvel.com/v1/public/characters",
        search,
        offset,
    )

    name = []
    description = []
    id = []
    img = []
    if len(data_results) == 0:
        return False

    for i in range(len(data_results)):
        name.append(data_results[i]["name"])
        if data_results[i]["description"] == "":
            description.append("No description available for this character.")
        else:
            description.append(data_results[i]["description"])
        id.append(data_results[i]["id"])
        imgPath = data_results[i]["thumbnail"]["path"]
        imgLink = imgPath + "/standard_fantastic.jpg"
        if imgLink == imgUnavailable:
            img.append("/static/comic error message.png")
        else:
            img.append(imgLink)
    return (id, name, description, img)


# Helper function to fetch the id of a creator to feed into the getComicByCreator function.
def getCreatorID(search):
    data_results = getJSONData(
        "nameStartsWith", "https://gateway.marvel.com/v1/public/creators", search
    )
    return data_results[0]["id"]


def getComicById(id):
    url = f"https://gateway.marvel.com/v1/public/comics/{id}"
    imgUnavailable = "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    params = {"ts": ts, "apikey": public_key, "hash": hashhex, "comicid": id}
    endpoint_request = requests.get(url=url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]
    creatorList = []
    title = data_results[0]["title"]
    onSaleDate = data_results[0]["dates"][0]["date"]
    buyLink = data_results[0]["urls"][0]["url"]
    imgPath = data_results[0]["thumbnail"]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"
    if imgLink == imgUnavailable:
        img = "/static/comic error message.png"
    else:
        img = imgLink
    creators = data_results[0]["creators"]["items"]
    for i in range(len(creators)):
        creatorList.append(data_results[0]["creators"]["items"][i]["name"])
    return title, creatorList, onSaleDate, img, buyLink


def getCharacterById(id):
    url = f"https://gateway.marvel.com/v1/public/characters/{id}"
    imgUnavailable = "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    params = {"ts": ts, "apikey": public_key, "hash": hashhex, "comicid": id}
    endpoint_request = requests.get(url=url, params=params)
    data = endpoint_request.json()
    data_results = data["data"]["results"]

    name = data_results[0]["name"]
    if data_results[0]["description"] == "":
        description = "No description available for this character."
    else:
        description = data_results[0]["description"]
    imgPath = data_results[0]["thumbnail"]["path"]
    imgLink = imgPath + "/standard_fantastic.jpg"
    if imgLink == imgUnavailable:
        img = "/static/comic error message.png"
    else:
        img = imgLink

    return name, description, imgLink
