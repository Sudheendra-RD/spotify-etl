from flask import Flask, request, redirect, jsonify, make_response, render_template
import requests
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
CLIENT_ID = 'e37f54312f9144859f28795ab3696469'  # Replace with your client ID
CLIENT_SECRET = '5fdfc2b2daf443e486ec8ec7a765b2ea'  # Replace with your client secret
REDIRECT_URI = 'http://localhost:8889/callback'  # Replace with your redirect URI

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

@app.route('/submit', methods=['POST'])
def get_user_playlist():
    user_input = request.form.get('user_input')
    return getArtistData.get_artist_data(user_input)
    
    # with open("access_token.txt", "r") as file:
    #     token = file.read().strip()
    # artist_id = '7uIbLdzzSEqnX0Pkrb56cR'
    # url = f"{GET_ARTIST_DATA}/{artist_id}/top-tracks"
    # artist_tract = requests.get(
    #     url,
    #     headers={'Authorization': f'Bearer {token}'}
    # )
    # saved_json = artist_tract.json()
    # for name in table_name:
    #     create_table(name, saved_json)

    # # push_data_to_mysql(saved_json)
    # return saved_json

db_config_with_db = {
        'host': 'localhost',
        'user': 'root',
        'password': 'sud@SQL_24',
        'database': 'spotify_db'  # Specify the newly created database
    }

table_name = ['albums', 'artists', 'tracks', 'album_artists', 'track_artists', 'album_markets', 'markets', 'track_markets']

def create_table(table_name, saved_json):
    connection = None
    connection = mysql.connector.connect(**db_config_with_db)
    cursor = connection.cursor()
    try:
        # Connect to the MySQL server with the new database
        if connection:
            match table_name:
                case 'albums':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        album_id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        album_type VARCHAR(50) NOT NULL,
                        release_date DATE,
                        release_date_precision VARCHAR(10),
                        total_tracks INT,
                        is_playable BOOLEAN,
                        spotify_url VARCHAR(255),
                        uri VARCHAR(255)
                    )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'album_artists':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        album_id VARCHAR(255),
                        artist_id VARCHAR(255),
                        PRIMARY KEY (album_id, artist_id),
                        FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,
                        FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
                    )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'artists':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        artist_id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        type VARCHAR(50),
                        spotify_url VARCHAR(255),
                        uri VARCHAR(255)
                    )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'track_artists':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        track_id VARCHAR(255),
                        artist_id VARCHAR(255),
                        PRIMARY KEY (track_id, artist_id),
                        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
                        FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
                    )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'tracks':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        track_id VARCHAR(255) PRIMARY KEY,
                        album_id VARCHAR(255),
                        name VARCHAR(255) NOT NULL,
                        disc_number INT,
                        track_number INT,
                        duration_ms INT,
                        explicit BOOLEAN,
                        popularity INT,
                        is_playable BOOLEAN,
                        is_local BOOLEAN,
                        spotify_url VARCHAR(255),
                        uri VARCHAR(255),
                        isrc VARCHAR(50),
                        FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE SET NULL
                        )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'markets':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        market_code CHAR(2) PRIMARY KEY,
                        market_name VARCHAR(255)
                        )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'album_markets':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        album_id VARCHAR(255),
                        market_code CHAR(2),
                        PRIMARY KEY (album_id, market_code),
                        FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE,
                        FOREIGN KEY (market_code) REFERENCES markets(market_code) ON DELETE CASCADE
                        )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
                case 'track_markets':
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        track_id VARCHAR(255),
                        market_code CHAR(2),
                        PRIMARY KEY (track_id, market_code),
                        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
                        FOREIGN KEY (market_code) REFERENCES markets(market_code) ON DELETE CASCADE
                        )
                    """
                    # Create the table if it doesn't exist
                    cursor.execute(create_table_query)
                    print(f"Table '{table_name}' created or already exists.")

                    # Commit changes
                    connection.commit()
                    insert_data_in_table(saved_json, table_name)
                    return
            print('papa')
    except Error as e:
        print(f"Error: {e}")
    finally:
        # if connection.is_connected():
            cursor.close()
            connection.close()

def insert_data_in_table(data, table_name):
    connection = None
    connection = mysql.connector.connect(**db_config_with_db)
    cursor = connection.cursor()
    match table_name:
        case 'albums':
            for item in data['tracks']:
                insert_data_command = f"""
                    INSERT IGNORE albums (album_id, name, album_type, release_date, release_date_precision, total_tracks, is_playable, spotify_url, uri)
                    VALUES 
                    ('{item['album']['id']}', '{item['album']['name']}', '{item['album']['album_type']}', '{item['album']['release_date']}', '{item['album']['release_date_precision']}', {item['album']['total_tracks']}, {item['album']['is_playable']}, '{item['album']['href']}', '{item['album']['uri']}');
                    """
                cursor.execute(insert_data_command)
                connection.commit()
            
            return
        case 'album_artists':
            for item in data['tracks']:
                for value in item['album']['artists']:
                    insert_data_command = f"""
                    INSERT IGNORE album_artists (album_id, artist_id)
                    VALUES 
                    ('{item['album']['id']}', '{value['id']}');
                    """
                cursor.execute(insert_data_command)
                connection.commit()
            return
        case 'artists':
            for item in data['tracks']:
                for value in item['artists']:
                    insert_data_command = f"""
                    INSERT IGNORE artists (artist_id, name, type, spotify_url, uri)
                    VALUES 
                    ('{value['id']}', '{value['name']}', '{value['type']}', '{value['href']}', '{value['uri']}');
                    """
                cursor.execute(insert_data_command)
                connection.commit()
            return
        case 'track_artists':
            for item in data['tracks']:
                track_id = item['id']
                for value in item['artists']:
                    insert_data_command = f"""
                    INSERT IGNORE track_artists (track_id, artist_id)
                    VALUES 
                    ('{track_id}', '{value['id']}');
                    """
                cursor.execute(insert_data_command)
                connection.commit()
            return
        case 'tracks':
            for item in data['tracks']:
                insert_data_command = f"""
                INSERT IGNORE tracks (track_id, album_id, name, disc_number, track_number, duration_ms, explicit, popularity, is_playable, is_local, spotify_url, uri, isrc)
                VALUES 
                ('{item['id']}', '{item['album']['id']}', '{item['name']}', {item['disc_number']}, {item['track_number']}, {item['duration_ms']}, {item['explicit']}, {item['popularity']}, {item['is_playable']}, {item['is_local']}, '{item['href']}', '{item['uri']}', '{item['external_ids']['isrc']}');
                """

                cursor.execute(insert_data_command)
                connection.commit()
            return
        case 'album_markets':
            for item in data['tracks']:
                for market in item['album']['available_markets']:
                    insert_data_command = f"""
                    INSERT IGNORE album_markets (album_id, market_code)
                    VALUES 
                    ('{item['album']['id']}', '{market}');
                    """
                    cursor.execute(insert_data_command)
                    connection.commit()
            return
        case 'markets':
            
            return
        case 'track_markets':
            for item in data['tracks']:
                for market in item['available_markets']:
                    insert_data_command = f"""
                    INSERT IGNORE track_markets (track_id, market_code)
                    VALUES 
                    ('{item['id']}', '{market}');
                    """
                    cursor.execute(insert_data_command)
                    connection.commit()
            return
    return
if __name__ == '__main__':
    app.run(port=8889, debug=True)
