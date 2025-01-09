from api_config import SEARCH_SPOTIFY_ARTIST
import requests, json

class GetArtistData:
    
    def __init__(self):
        with open("access_token.txt", "r") as file:
            token = file.read().strip()
            self.headers = {'Authorization': f'Bearer {token}'}
            self.get_artist_data('')

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