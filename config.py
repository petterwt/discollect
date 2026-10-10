import os
from dotenv import load_dotenv

# load .env before reading any variables
load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

class Config:
    # grabs the variables from .env file, keeping pw safe
    SECRET_KEY = os.environ.get("SECRET_KEY") # needed for session protection in flask (XSRF)

    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_NAME = os.environ.get("DB_NAME")