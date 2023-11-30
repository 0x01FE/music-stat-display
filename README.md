# About

This is a front end web display for [this](https://github.com/0x01FE/spotify-artist-time-tracking) other project of mine.

These two projects work together to track and display Spotify listening data.


# Config File Format
This program uses a config.ini file for some basic variables. This is an example of how I have mine set up.

```ini
[PATHES]
templates=./templates/
database=./data/spotify-listening-data.db

[NETWORK]
port=5000
```

If you are connecting this program to the [Spotify Time Tracking Project](https://github.com/0x01FE/spotify-artist-time-tracking) the database path should point to a volume mount that is the same volume mount that the Spotify Time Tracking container uses.

# Setup

This program was designed to be used with Docker containers.

## Docker


Run this docker command to build the image.

```sh
docker build . -t music-stat-display:v3
```

After that configure the example docker compose file in the repo and run,
```sh
docker compose up
```
Add the -d flag if you want it to run in the background.
