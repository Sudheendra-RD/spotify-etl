from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import pandas as pd
import matplotlib.pyplot as plt
import re, json

spotify_client_id = "e37f54312f9144859f28795ab3696469"
spotify_client_secret = "5fdfc2b2daf443e486ec8ec7a765b2ea"
# Set up Cliennt Credentials
spotify_credential = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id,client_secret=spotify_client_secret))

# Define the track url from any song from Spotify
track_url = "https://open.spotify.com/track/5RaK2eqyHaBSyjEtI27w3T?si=aa076e6ff8594c36"

# Get the trackID from the above URL
track_id = re.search(r"track/([^/?]+)", track_url).group(1)

# Get the track details using the spotify creden
track = spotify_credential.track(track_id)

# Get the required data from the metadata provided by the SPotify API
track_data = {
    'Track Name': track['name'],
    'Artist': track['artists'][0]['name'],
    'Album': track['album']['name'],
    'Popularity': track['popularity'],
    'Duration (minutes)': track['duration_ms'] / 60000
}

# The data is provided as a JSON. To view the data in a readable format, uncomment the below line
# print(json.dumps(track, indent=3))

# convert the data into dataframe
df = pd.DataFrame([track_data])

# Save the dataframe into CSV
df.to_csv('spotify_data.csv', index=False)

# Visualise the track_data using matplotlib
features = ['Popularity', 'Duration (minutes)']
values = [track_data['Popularity'], track_data['Duration (minutes)']]

plt.figure(figsize=(8, 5))
plt.bar(features, values, color='skyblue', edgecolor='black')
plt.title(f"Track Metadata for '{track_data['Track Name']}'")
plt.ylabel('Value')
plt.savefig('plot.png')