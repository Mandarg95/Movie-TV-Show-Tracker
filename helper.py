import csv
import datetime
import pytz
import requests
import urllib
import uuid

from flask import redirect, render_template, request, session
from functools import wraps

TMDB_API_KEY = '467129e714b8545fa30895f786855903'

def search_media(query):
    url = f'https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def fetch_info(media,id):
    url = f'https://api.themoviedb.org/3/{media}/{id}?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def fetch_top_rated(media_type):
    """Fetch top-rated media from TMDB based on media type (movie or tv)"""
    url = f"https://api.themoviedb.org/3/{media_type}/top_rated?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['results']
    else:
        return []


def fetch_media():
    url = f'https://api.themoviedb.org/3/trending/all/week?api_key={TMDB_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def fetch_popular(media_type):
    """Fetch popular movies or TV shows based on the media_type"""
    url = f"https://api.themoviedb.org/3/{media_type}/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code



def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
