-- Top Albums
SELECT
	artist_name,
	artist_id,
	album_name,
	cover_art_url,
	SUM(time) time,
	album_spotify_id
FROM
	(SELECT
		artists.name artist_name,
		artists.id artist_id,
		albums.name album_name,
		songs.name song_name,
		SUM("listen-events".time) / COUNT(DISTINCT artists.id) time,
		albums.id album_id,
		albums.spotify_id album_spotify_id,
		albums.cover_art_url cover_art_url
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	INNER JOIN albums on songs.album=albums.id
	WHERE
		"listen-events".user = ?
	GROUP BY
		"listen-events".song)
GROUP BY
	album_id
ORDER BY
	time DESC;

-- Top Albums with date range
SELECT
	artist_name,
	artist_id,
	album_name,
	cover_art_url,
	SUM(time) time,
	album_spotify_id
FROM
	(SELECT
		artists.name artist_name,
		artists.id artist_id,
		albums.name album_name,
		songs.name song_name,
		SUM("listen-events".time) / COUNT(DISTINCT artists.id) time,
		albums.id album_id,
		albums.spotify_id album_spotify_id,
		albums.cover_art_url cover_art_url
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	INNER JOIN albums on songs.album=albums.id
	WHERE
		"listen-events".user = ?
		AND DATE("listen-events".date) BETWEEN ? AND ?
	GROUP BY
		"listen-events".song)
GROUP BY
	album_id
ORDER BY
	time DESC;
