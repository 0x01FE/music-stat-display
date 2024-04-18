-- Top Played Songs
SELECT
	*,
	SUM(1) count
FROM
	(SELECT
		songs.artist,
		artists.name,
		artists.icon_url,
		artists.spotify_id
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	WHERE
		user = ?)
GROUP BY
	artist
ORDER BY
	count DESC;

-- Top Played Songs with date range
SELECT
	*,
	SUM(1) count
FROM
	(SELECT
		songs.artist,
		artists.name,
		artists.icon_url,
		artists.spotify_id
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	WHERE
		user = ?
		AND DATE(date) BETWEEN ? AND ?)
GROUP BY
	artist
ORDER BY
	count DESC;