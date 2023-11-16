-- Top Plays
SELECT
	artists.name artist_name,
	artists.id artist_id,
	songs.name,
	songs.id,
	COUNT(song) / COUNT (DISTINCT songs.artist) plays
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	user = ?
GROUP BY
	songs.id
ORDER BY
	plays DESC;

-- Top Plays with date range
SELECT
	artists.name artist_name,
	artists.id artist_id,
	songs.name,
	songs.id,
	COUNT(song) / COUNT (DISTINCT songs.artist) plays
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	user = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?
GROUP BY
	songs.id
ORDER BY
	plays DESC;

-- Top Plays for artist
SELECT
	songs.name,
	songs.id,
	COUNT(song) / COUNT (DISTINCT songs.artist) plays
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	user = ?
	AND songs.artist = ?
GROUP BY
	songs.id
ORDER BY
	plays DESC;