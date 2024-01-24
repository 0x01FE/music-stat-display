import json

import spotipy

from spotipy.oauth2 import SpotifyOAuth

import db

SCOPES = "user-read-playback-state user-read-currently-playing user-top-read user-read-recently-played user-read-playback-position"

"""
Represents a user, their connection to the spotify api, and their connection to the database.
"""
class User():


    id : int
    name : str
    wait_time : int
    api : spotipy.Spotify


    def __init__(self, id):
        self.id = id
        self.wait_time = 0

        spotify_id = self.get_spotify_id()

        # Setup API connection
        with open(f"./data/.{spotify_id}-cache", 'r') as f:
            cache_data = json.loads(f.read())

        cache_handler = spotipy.MemoryCacheHandler(
            token_info=cache_data)

        self.api = spotipy.Spotify(
            auth_manager = SpotifyOAuth(
                scope=SCOPES,
                cache_handler=cache_handler
            ))

    def __str__(self) -> str:
        return self.name


    # Database Methods


    """
    Get the database id for this user.
    Really only meant as an internal method but no reason to mark it as such.

    Parameters:
        None
    Returns:
        id (str) : id of this user in the database
    """
    def get_spotify_id(self) -> str:
        with db.Opener() as (con, cur):
            cur.execute("SELECT * FROM users WHERE id = ?", [self.id, ])

            results = cur.fetchall()

        return results[0][2]