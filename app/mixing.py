import configparser
import random
import os

import db
import query
import daterange



MAX_ARTIST_SONGS = 7

config = configparser.ConfigParser()

dev = False
if 'env' in os.environ:
    dev = os.environ['env'] == 'DEV'

if dev:
    config.read("config-dev.ini")
else:
    config.read("config.ini")

SQL_DIR = config['PATHES']['SQL']



"""
Should returns a list of track URIs for a playlist


Mixing Algo:

 1. Get top artists for _this_ month
 2. Pull 


"""
def alt_mix(user_id : int) -> list:

    # Get top artists for the month
    period = daterange.this_month()

    # Set Up queries
    q = query.Query(SQL_DIR + 'data/top_artists_weight.sql')

    args = {2 : (user_id, period.sstart(), period.send())}

    top_artist_songs_q = query.Query(SQL_DIR + 'data/top_artist_songs.sql')

    top_artists = q.execute(args)



    playlist = [] # just IDs, no URIs yet

    artists_limit = random.randint(4, 7)

    for artist in top_artists[:artists_limit]:

        artist_id = artist[1]
        song_index = 0
        songs_added = 0
        artist_weight = artist[-1]

        top_artist_songs = top_artist_songs_q.forceExecuteSingle(1, [user_id, artist_id, period.sstart(), period.send()])

        for song in top_artist_songs:
            num = random.randint(1, 100) / 100.0

            if song_index == 0:
                playlist.append(song)
                songs_added += 1
            elif song_index == 1:
                if num <= 0.5:
                    playlist.append(song)
                    songs_added += 1
            else:
                if num <= artist_weight - (3 * songs_added / 100.0):
                    playlist.append(song)
                    songs_added += 1
                else:
                    break
            song_index += 1


        # print(top_artist_songs)

    for song in playlist:
        print(song[1])
    print(len(playlist))

    # print(top_artists)

def add_weights(weights: list, others: list) -> list:
    new_weights = []

    # Add duplicate item weights
    for other_weight in others:
        for weight in weights:
            if weight[1] == other_weight[1]:
                new_weights.append((weight[1], weight[-1] + other_weight[-1]))

    # Add missing weights
    for weight_list in [weights, others]:
        for weight in weight_list:
            found = False
            for new_weight in new_weights:
                if weight[1] == new_weight[1]:
                    found = True

            if not found:
                new_weights.append(weight)

    return new_weights

def mix_songs(weights : list) -> list:
    playlist = []

    for song in weights:
        weight: float = song[-1]

        P = random.randint(0, 100) / 100.0

        if P <= weight:
            playlist.append(song)

    return playlist

alt_mix(1)




