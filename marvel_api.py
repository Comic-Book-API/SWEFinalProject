"""https://stackoverflow.com/questions/53356636/invalid-hash-timestamp-and-key-
# combination-in-marvel-api-call helped me get the api calls to work"""

import os
import hashlib
import time
from dotenv import find_dotenv, load_dotenv
import requests

load_dotenv(find_dotenv())

public_key = os.getenv("marvel_public_key")
private_key = os.getenv("marvel_private_key")

local_hash = (
    hashlib.md5()
)  # w5 algorithm of the ts, public key, and private key mashed together
# To do this, I made ts a random time, converted ts, public key,
# and private key into byte format so they can be fed into the md5 formatter,
# and then convert the hashed string into the hex form,
# which is the form required by the Marvel API.
TS = str(time.time())
ts_byte = bytes(TS, "utf-8")
public_byte = bytes(public_key, "utf-8")
private_byte = bytes(private_key, "utf-8")
local_hash.update(ts_byte)
local_hash.update(private_byte)
local_hash.update(public_byte)
HASHHEX = local_hash.hexdigest()

urlAddOn = f"?ts={TS}&apikey={public_key}&local_hash={HASHHEX}"

last_call_time = 0


def get_data(url, params):
    """# function to get data from the API.
# It uses a timer to make sure that it never calls more than once"""
    global last_call_time
    if time.time() - last_call_time > 0.5:

        endpoint_request = requests.get(url=url, params=params)
        last_call_time = time.time()
        data = endpoint_request.json()
        print("made an api call")
        if isinstance(
                data, int
        ):  # sometimes the marvel api just sends back an
            # int for the comic or character id. Server side bug?
            print("!!GETDATA GOT INT!!")
            return get_data(url, params)
        return data
    else:
        time.sleep(0.5)
        return get_data(url, params)


def get_json_data(search_field, url, search, offset):
    """init method for api calls"""
    if search_field == "nameStartsWith":
        limit = 100
        params = {
            "ts": TS,
            "apikey": public_key,
            "hash": HASHHEX,
            f"{search_field}": search,
            "limit": limit,
            "offset": offset,
        }
    else:
        limit = 10
        params = {
            "ts": TS,
            "apikey": public_key,
            "hash": HASHHEX,
            f"{search_field}": search,
            "limit": limit,
            "offset": offset,
            "noVariants": True,
        }
    data = get_data(url=url, params=params)
    try:
        data_results = data["data"]["results"]
        return data_results
    except KeyError:
        return False


def get_comic_by_title(search, offset):
    """returns comic by title if it exists"""
    data_results = get_json_data(
        "titleStartsWith", "https://gateway.marvel.com/v1/public/comics", search, offset
    )

    if not data_results:
        return False, False, False, False, False

    # Catch out of bounds error
    if len(data_results) == 0:
        return False, False, False, False, False
    # Returns the title, the on sale date of the comic,
    # a link to an image of the comic, and a list of
    # collaborators who worked on the comic.
    img_unavailable = \
        "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    title = []
    on_sale_date = []
    creator_list = []
    buy_link = []
    img = []
    creator_arr = []

    # For the API, we have to change the link returned by the json
    # or else it gives a permission denied error. To do this, we
    # just append a string onto the end that Marvel has pre-defined.
    # standard_fantastic is the version of the img we chose.
    img_path = data_results[0]["thumbnail"]["path"]
    img_link = img_path + "/standard_fantastic.jpg"

    if len(data_results) >= 10:
        for i in range(10):
            creator_list = []
            title.append(data_results[i]["title"])
            on_sale_date.append(data_results[i]["dates"][0]["date"])
            buy_link.append(data_results[i]["urls"][0]["url"])
            img_path = data_results[i]["thumbnail"]["path"]
            img_link = img_path + "/standard_fantastic.jpg"
            if img_link == img_unavailable:
                img.append("/static/comic error message.png")
            else:
                img.append(img_link)
            creators = data_results[i]["creators"]["items"]
            for j in range(len(creators)):
                creator_list.append(data_results[i]["creators"]["items"][j]["name"])
            creator_arr.append(creator_list)

    else:
        for i in range(len(data_results)):
            title.append(data_results[i]["title"])
            on_sale_date.append(data_results[i]["dates"][0]["date"])
            buy_link.append(data_results[i]["urls"][0]["url"])
            img_path = data_results[i]["thumbnail"]["path"]
            img_link = img_path + "/standard_fantastic.jpg"
            img.append(img_link)
            creators = data_results[i]["creators"]["items"]
            for j in range(len(creators)):
                creator_list.append(data_results[i]["creators"]["items"][j]["name"])
            creator_arr.append(creator_list)
    return title, creator_arr, on_sale_date, img, buy_link


def get_comic_by_character(search, offset):
    """Because the parameter must be a character ID, we have to make a call to
    # getCharacters so we can have the ID of the search query. From there,
    # it's passed into the parameters to perform the search"""
    (local_id, name, description, img_link) = get_character(search, 0)
    data_results = get_json_data(
        "characters", "https://gateway.marvel.com/v1/public/comics", local_id, offset
    )
    if not data_results:
        return False, False, False, False, False

    title = data_results[0]["title"]

    return get_comic_by_title(title, offset)


def get_comic_by_creator(search, offset):
    """# We can't search for the creator by name.
    # It has to be by ID, so we need to call the helper function that
    will return the creator id of the search query/"""
    creator = get_creator_id(search)
    data_results = get_json_data(
        "creators", "https://gateway.marvel.com/v1/public/comics", creator, offset
    )
    if not data_results:
        return False, False, False, False, False

    title = data_results[0]["title"]

    return get_comic_by_title(title, offset)


def get_series(search, offset):
    """# Not sure what we're going to do with this yet,
    but it doesn't hurt to include it."""
    data_results = get_json_data(
        "titleStartsWith", "https://gateway.marvel.com/v1/public/series", search, offset
    )
    if not data_results:
        return False, False, False, False, False
    title_list = []
    for i in range(len(data_results)):
        title_list.append(data_results[i]["title"])

    return title_list


def get_character(search, offset):
    """core functionality searching method for characters"""
    img_unavailable = \
        "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    data_results = get_json_data(
        "nameStartsWith",
        "https://gateway.marvel.com/v1/public/characters",
        search,
        offset,
    )
    if not data_results:
        return False, False, False, False

    name = []
    description = []
    local_id = []
    img = []
    if len(data_results) == 0:
        return False, False, False, False

    for i in range(len(data_results)):
        name.append(data_results[i]["name"])
        if data_results[i]["description"] == "":
            description.append("No description available for this character.")
        else:
            description.append(data_results[i]["description"])
        local_id.append(data_results[i]["id"])
        img_path = data_results[i]["thumbnail"]["path"]
        img_link = img_path + "/standard_fantastic.jpg"
        if img_link == img_unavailable:
            img.append("/static/comic error message.png")
        else:
            img.append(img_link)
    return local_id, name, description, img


def get_creator_id(search):
    """# Helper function to fetch the id of a creator
    to feed into the get_comic_by_creator function."""
    data_results = get_json_data(
        "nameStartsWith", "https://gateway.marvel.com/v1/public/creators", search, 0
    )
    if not data_results:
        return False, False, False, False, False
    return data_results[0]["id"]


def get_comic_by_id(inp_id):
    """searching method based on user inputted comic id.
        checks for missing info from marvel api,
        and fills in placeholder data for it"""
    url = f"https://gateway.marvel.com/v1/public/comics/{inp_id}"
    img_unavailable = \
        "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    params = {"ts": TS, "apikey": public_key, "hash": HASHHEX, "comicId": inp_id}
    data = get_data(url=url, params=params)
    try:
        data_results = data["data"]["results"]
    except:
        print(data)
        return False, False, False, False, False
    creator_list = []
    title = data_results[0]["title"]
    on_sale_date = data_results[0]["dates"][0]["date"]
    buy_link = data_results[0]["urls"][0]["url"]
    img_path = data_results[0]["thumbnail"]["path"]
    img_link = img_path + "/standard_fantastic.jpg"
    if img_link == img_unavailable:
        img = "/static/comic error message.png"
    else:
        img = img_link
    creators = data_results[0]["creators"]["items"]
    for i in range(len(creators)):
        creator_list.append(data_results[0]["creators"]["items"][i]["name"])
    return title, creator_list, on_sale_date, img, buy_link


def get_character_by_id(inp_id):
    """searching method based on user inputted character id.
    checks for missing info from marvel api,
    and fills in placeholder data for it"""
    url = f"https://gateway.marvel.com/v1/public/characters/{inp_id}"
    img_unavailable = \
        "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
    params = {"ts": TS, "apikey": public_key, "hash": HASHHEX, "characterId": inp_id}
    data = get_data(url=url, params=params)
    try:
        data_results = data["data"]["results"]
    except KeyError:
        return False, False, False

    name = data_results[0]["name"]
    if data_results[0]["description"] == "":
        description = "No description available for this character."
    else:
        description = data_results[0]["description"]
    img_path = data_results[0]["thumbnail"]["path"]
    img_link = img_path + "/standard_fantastic.jpg"
    if img_link == img_unavailable:
        img_link = "/static/comic error message.png"

    return name, description, img_link
