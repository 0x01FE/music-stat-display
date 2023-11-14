-- Top Albums
SELECT
	artist_name,
	album_name,
	SUM(time) time
FROM
	(SELECT
		artists.name artist_name,
		albums.name album_name,
		songs.name song_name,
		SUM("listen-events".time) / COUNT(DISTINCT artists.id) time
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
	album_name
ORDER BY
	time DESC;

-- Top Albums with date range
SELECT
	artist_name,
	album_name,
	SUM(time) time
FROM
	(SELECT
		artists.name artist_name,
		albums.name album_name,
		songs.name song_name,
		SUM("listen-events".time) / COUNT(DISTINCT artists.id) time
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
	album_name
ORDER BY
	time DESC;
