from flask import Flask, request, redirect, jsonify, make_response, render_template
import requests, asyncio
import os
import base64
import secrets
import urllib.parse
import json
import logging
import mysql.connector
from mysql.connector import Error
from get_artist_data import GetArtistData


app = Flask(__name__)

# Spotify credentials
CLIENT_ID = 'your_client_id'  # Replace with your client ID
CLIENT_SECRET = 'your_client_secret'  # Replace with your client secret
REDIRECT_URI = '-------------------'  # Replace with your redirect URI

# Spotify API endpoints
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
USER_PROFILE_URL = 'https://api.spotify.com/v1/me'
GET_ARTIST_DATA = 'https://api.spotify.com/v1/artists'

STATE_KEY = 'spotify_auth_state'

getArtistData = GetArtistData()

# Utility function to generate a random string for state
def generate_random_string(length):
    return secrets.token_hex(length // 2)

@app.route('/login')
def login():
    state = generate_random_string(16)
    build_url = urllib.parse.urlencode({  # Build the authorization URL
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': 'user-read-private user-read-email',
        'redirect_uri': REDIRECT_URI,
        'state': state
    })
    response = make_response(redirect(f"{AUTH_URL}?{build_url}"))
    response.set_cookie(STATE_KEY, state)  # Store state in a cookie
    return response


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    stored_state = request.cookies.get(STATE_KEY)

    # Verify the state parameter
    if state is None or state != stored_state:
        return redirect('/?error=state_mismatch')

    # Exchange authorization code for access and refresh tokens
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_response = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
        },
        headers={
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )

    if token_response.status_code != 200:
        return redirect('/?error=invalid_token')

    tokens = token_response.json()
    access_token = tokens['access_token']
    with open('access_token.txt', 'w') as f:
            f.write(access_token)
    refresh_token = tokens['refresh_token']

    # Use the access token to get user profile data
    user_response = requests.get(
        USER_PROFILE_URL,
        headers={'Authorization': f'Bearer {access_token}'}
    )

    user_data = user_response.json()
    # Redirect back with tokens and user data
    # return jsonify({
    #     'access_token': access_token,
    #     'refresh_token': refresh_token,
    #     'user': user_data
    # })
    return render_template('index.html')

@app.route('/refresh_token')
def refresh_token():
    refresh_token = request.args.get('refresh_token')

    # Request a new access token using the refresh token
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_response = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        },
        headers={
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )

    if token_response.status_code != 200:
        return jsonify({'error': 'Unable to refresh token'}), 400

    tokens = token_response.json()
    access_token = tokens['access_token']
    os.environ['SPOTIFY_ACCESS_TOKEN'] = access_token
    return jsonify({
        'access_token': tokens['access_token']
    })

get_spotify_token = os.getenv('SPOTIFY_ACCESS_TOKEN')

table_name = ['albums', 'artists', 'tracks']
@app.route('/submit', methods=['POST'])
def get_user_playlist():
    user_input = request.form.get('user_input')

    if user_input:
        artist_id = getArtistData.get_artist_data(user_input)
        # return artist_id

    try:
        artist_track = asyncio.run(getArtistData.get_artist_tracks(artist_id))
        for item in table_name:
            getArtistData.create_table(item, artist_track)
        return jsonify(f"Data Inserted successfully. Please check the MySQL workbenck")
    except Exception as e:
        return jsonify(f"Failed to fetch artist tracks with an error: {e}")

if __name__ == '__main__':
    app.run(port=8889, debug=True)
