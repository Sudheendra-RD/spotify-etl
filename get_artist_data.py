from api_config import GET_ARTIST_DATA, SEARCH_SPOTIFY_ARTIST
import requests, json, httpx
import mysql.connector
from mysql.connector import Error

class GetArtistData:
    
    def __init__(self):
        with open("access_token.txt", "r") as file:
            token = file.read().strip()
            self.headers = {'Authorization': f'Bearer {token}'}
            self.db_config_with_db = {
                'host': 'localhost',
                'user': 'root',
                'password': 'sud@SQL_24',
                'database': 'spotify_db'  # Specify the newly created database
            }

    def get_artist_data(self, artist_name):
        artist_name_with_out_space = artist_name.replace(" ", "+")
        api_url = f"{SEARCH_SPOTIFY_ARTIST}?q={artist_name_with_out_space}&type=artist&limit=1&offset=0"
        fetch_artist_data = requests.get(api_url, headers=self.headers)
        artist_data = fetch_artist_data.json()
        artist_items = artist_data.get('artists', {}).get('items', [])
        if not artist_items:
            print("No artist found.")
            return None

        # Extract artist ID
        artist_id = artist_items[0].get('id')
        return artist_id
    
    async def get_artist_tracks(self, artist_id):
        url = f"{GET_ARTIST_DATA}/{artist_id}/top-tracks?market=IN"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code!= 200:
                return {"error": "Failed to fetch artist tracks"}
            return response.json()
    
    def create_table(self, table_name, saved_json):
        connection = None
        connection = mysql.connector.connect(**self.db_config_with_db)
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
                        self.insert_data_in_table(saved_json, table_name)
                        return
                    case 'artists':
                        create_table_query = f"""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            artist_id VARCHAR(255) PRIMARY KEY,
                            album_id VARCHAR(255),
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
                        self.insert_data_in_table(saved_json, table_name)
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
                        self.insert_data_in_table(saved_json, table_name)
                        return
        except Error as e:
            print(f"Error: {e}")
        finally:
            # if connection.is_connected():
                cursor.close()
                connection.close()

    def insert_data_in_table(self, data, table_name):
        connection = None
        connection = mysql.connector.connect(**self.db_config_with_db)
        cursor = connection.cursor()
        match table_name:
            case 'albums':
                try:
                    for item in data['tracks']:
                        insert_data_command = f"""
                            INSERT IGNORE albums (album_id, name, album_type, release_date, release_date_precision, total_tracks, is_playable, spotify_url, uri)
                            VALUES 
                            ('{item['album']['id']}', '{item['album']['name']}', '{item['album']['album_type']}', '{item['album']['release_date']}', '{item['album']['release_date_precision']}', {item['album']['total_tracks']}, {item['album']['is_playable']}, '{item['album']['external_urls']['spotify']}', '{item['album']['uri']}');
                            """
                        cursor.execute(insert_data_command)
                        connection.commit()
                    return
                except Exception as e:
                    print(f"Could not insert value in table {table_name} due to error {e}")
            case 'artists':
                try:
                    for item in data['tracks']:
                        for value in item['album']['artists']:
                            insert_data_command = f"""
                            INSERT IGNORE artists (artist_id, album_id, name, type, spotify_url, uri)
                            VALUES 
                            ('{value['id']}', '{item['album']['id']}', '{value['name']}', '{value['type']}', '{value['href']}', '{value['uri']}');
                            """
                        cursor.execute(insert_data_command)
                        connection.commit()
                    return
                except Exception as e:
                    print(f"Could not insert value in table {table_name} due to error {e}")
            case 'tracks':
                try:
                    for item in data['tracks']:
                        insert_data_command = f"""
                        INSERT IGNORE tracks (track_id, album_id, name, disc_number, track_number, duration_ms, explicit, popularity, is_playable, is_local, spotify_url, uri, isrc)
                        VALUES 
                        ('{item['id']}', '{item['album']['id']}', '{item['name']}', {item['disc_number']}, {item['track_number']}, {item['duration_ms']}, {item['explicit']}, {item['popularity']}, {item['is_playable']}, {item['is_local']}, '{item['href']}', '{item['uri']}', '{item['external_ids']['isrc']}');
                        """

                        cursor.execute(insert_data_command)
                        connection.commit()
                    return
                except Exception as e:
                    print(f"Could not insert value in table {table_name} due to error {e}")
        return
