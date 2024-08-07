-- Top Artists
SELECT
    artist_name,
	artist_id,
	artist_spotify_id,
	icon_url,
    sum(time)
FROM
    (SELECT
        artists.name artist_name,
		artists.id artist_id,
        songs.name song_name,
        SUM("listen-events".time) time,
		artists.spotify_id artist_spotify_id,
		artists.icon_url icon_url
    FROM
        "listen-events"
    INNER JOIN songs ON "listen-events".song=songs.id
    INNER JOIN artists ON songs.artist=artists.id
    WHERE
        "listen-events".user = ?
    GROUP BY
        "listen-events".song,
        songs.artist)
GROUP BY
    artist_name
ORDER BY
    SUM(time) DESC;

-- Top Artists with date range
SELECT
    artist_name,
	artist_id,
	artist_spotify_id,
	icon_url,
    sum(time)
FROM
    (SELECT
        artists.name artist_name,
		artists.id artist_id,
        songs.name song_name,
        SUM("listen-events".time) time,
		artists.spotify_id artist_spotify_id,
		artists.icon_url icon_url
    FROM
        "listen-events"
    INNER JOIN songs ON "listen-events".song=songs.id
    INNER JOIN artists ON songs.artist=artists.id
    WHERE
        "listen-events".user = ?
        AND DATE("listen-events".date) BETWEEN ? AND ?
    GROUP BY
        "listen-events".song,
        songs.artist)
GROUP BY
    artist_name
ORDER BY
    SUM(time) DESC;
