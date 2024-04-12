-- Top Songs
SELECT
	artist_name,
	artist_id,
	song_name,
	cover_art_url,
	album_spotify_id,
	MIN(time) time
FROM
	(SELECT
		artists.name artist_name,
		artists.id artist_id,
		songs.name song_name,
		songs.id song_id,
		SUM("listen-events".time) time,
		albums.cover_art_url cover_art_url,
		albums.spotify_id album_spotify_id
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	INNER JOIN albums ON songs.album=albums.id
	WHERE
		"listen-events".user = ?
	GROUP BY
		artists.id,
		songs.id
	ORDER BY
		time DESC)
GROUP BY
	song_id
ORDER BY
	time DESC;

-- Top Songs with date range
SELECT
	artist_name,
	artist_id,
	song_name,
	cover_art_url,
	album_spotify_id,
	MIN(time) time
FROM
	(SELECT
		artists.name artist_name,
		artists.id artist_id,
		songs.name song_name,
		songs.id song_id,
		SUM("listen-events".time) time,
		albums.cover_art_url cover_art_url,
		albums.spotify_id album_spotify_id
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	WHERE
		"listen-events".user = ?
    	AND DATE("listen-events".date) BETWEEN ? AND ?
	GROUP BY
		artists.id,
		songs.id
	ORDER BY
		time DESC)
GROUP BY
	song_id
ORDER BY
	time DESC;
