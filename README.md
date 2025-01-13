This project is built using a Flask app, which takes the artist's name as input and fetches the top tracks for that artist.
The data is transformed to get the tracks, albums, and artists.
This data is then loaded into MySQL database.

🔑 Key Features of the Project:
Data Extraction: Leveraged Spotify's Web API to fetch Top Tracks of an artist.
Data Transformation: Processed and cleaned data using Python and SQL.
Data Storage: Stored data in MySQL database.

Steps to run this project:
- Create a Spotify Developer account with a redirect URL of your choice with a ‘/callback’ at the end (ex: ‘http://localhost:8000/callback’)
- Download the required Python packages in the requirements.txt file.
- Copy and paste the Client ID, Client Secret and Redirect URL in the get_auth_token.py file.
- Connect to MySQL server and create a schema.
- Copy and paste the username, password and schema name in the “db_config” of get_artist_data.py file.
- Run the get_auth_token.py file
- In the Chrome browser, go to the redirect URL.
- Enter the artist name and click Submit.
- Check the MySQL Workbench to see the data of that particular artist.
