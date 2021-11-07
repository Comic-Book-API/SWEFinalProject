import flask
import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

public_key = os.getenv("marvel_public_key")
private_key = os.getenv("marvel_private_key")
