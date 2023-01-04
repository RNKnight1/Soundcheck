import os
import base64
import requests
import json

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_caching import Cache
from urllib.parse import quote

# Configure application
app = Flask(__name__)


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    "TEMPLATES_AUTO_RELOAD": True,
    "SESSION_PERMANENT": False,
    "SESSION_TYPE": "filesystem"
}

app.config.from_mapping(config)

Session(app)
cache = Cache(app)

SPOT_ID = os.environ.get("SPOT_ID")
SPOT_SEC = os.environ.get("SPOT_SEC")
SCOPE = "user-library-modify,user-library-read,user-read-playback-position,user-top-read,user-read-recently-played,playlist-read-private,playlist-read-collaborative,playlist-modify-private,playlist-modify-public"
REDIRECT_URI = "http://127.0.0.1:5000/callback"
# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": SPOT_ID
}

'''
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
'''

@app.route("/landing")
def landing():
    return render_template("landing.html")

@app.route("/")
@cache.cached(unless=lambda x: not session.get("access_token"))
def index():
    if not session.get("access_token"):
        return redirect("/landing")
    
    else:
        try:
            authorization_header = {"Authorization": "Bearer {}".format(session["access_token"])}
            user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
            profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
            profile_data = json.loads(profile_response.text)
            username = profile_data['display_name']
            image_url = profile_data['images'][0]['url']
            top_data = [{'time_range' : 'short_term', 'limit' : 50}, {'time_range' : 'medium_term', 'limit' : 50}, {'time_range' : 'long_term', 'limit' : 50}]
            audio_features = []
            time_artist_lists = {}
            time_track_lists = {}
            for time_range in top_data:
                top_tr_response = requests.get(user_profile_api_endpoint + '/top/tracks', headers=authorization_header, params=time_range)
                top_ar_response = requests.get(user_profile_api_endpoint + '/top/artists', headers=authorization_header, params=time_range)
                time_track_lists[time_range['time_range']] = json.loads(top_tr_response.text)['items']
                time_artist_lists[time_range['time_range']] = json.loads(top_ar_response.text)['items']

            genre_list = {}
            for artist in time_artist_lists['long_term']:
                for genre in artist['genres']:
                    if genre not in genre_list.keys():
                        genre_list[genre] = 1
                    else:
                        genre_list[genre] += 1
            genre_list = sorted(genre_list.items(), key=lambda d: d[1], reverse=True)


            features_list = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            feature_track_list = []
            
            for track in time_track_lists['long_term']:
                features = requests.get(SPOTIFY_API_URL + '/audio-features/' + track['id'], headers=authorization_header).json()
                features['name'] = track['name']
                features['artist'] = track['artists'][0]['name']
                feature_track_list.append(features)
                features_list[0] += features['valence']
                features_list[1] += features['danceability']
                features_list[2] += features['energy']
                features_list[3] += features['tempo']
                features_list[4] += features['loudness']
                features_list[5] += features['speechiness']
                features_list[6] += features['instrumentalness']
                features_list[7] += features['liveness']
                features_list[8] += features['acousticness']

            valence_list = sorted(feature_track_list, key=lambda d: d['valence'], reverse=True)
            danceability_list = sorted(feature_track_list, key=lambda d: d['danceability'], reverse=True)
            energy_list = sorted(feature_track_list, key=lambda d: d['energy'], reverse=True)
            tempo_list = sorted(feature_track_list, key=lambda d: d['tempo'], reverse=True)
            list_dict = {'valence': valence_list, 'danceability': danceability_list, 'energy': energy_list, 'tempo': tempo_list}
            for i in range(3):
                features_list[i] = round(features_list[i] * 10) 
            for i in range(9)[3:]:
                features_list[i] = round(features_list[i] / 50, 3)

            return render_template("index.html", username=username, image_url=image_url, top_tracks=time_track_lists, top_artists=time_artist_lists, features=features_list, list_dict=list_dict, genre_list=genre_list)
        except KeyError:
            session.clear()
            return redirect("/login")

@app.route("/login")
def login():
    auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": SPOT_ID
    }
    url_args = f"response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}&client_id={SPOT_ID}"
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/loading")
def loading():
    return render_template("loading.html")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(code),
        "redirect_uri": REDIRECT_URI,
        'client_id': SPOT_ID,
        'client_secret': SPOT_SEC,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    session["access_token"] = access_token
    return redirect("/loading")

@app.route("/error")
def error():
    return render_template("error.html")