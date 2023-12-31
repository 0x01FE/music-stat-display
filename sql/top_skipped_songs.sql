-- Top Skipped Songs
SELECT
	songs.artist,
	artists.name artist_name,
	songs.name,
	COUNT(skip) skips
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists on songs.artist=artists.id
WHERE
	user = ?
	AND skip = 1
GROUP BY
	song
ORDER BY
	skips DESC;

-- Top Skipped Songs with date range
SELECT
	songs.artist,
	artists.name artist_name,
	songs.name,
	COUNT(skip) skips
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists on songs.artist=artists.id
WHERE
	user = ?
	AND skip = 1
    AND DATE(date) BETWEEN ? AND ?
GROUP BY
	song
ORDER BY
	skips DESC;


-- Top Skipped Songs with artist
SELECT
	songs.artist,
	artists.name artist_name,
	songs.name,
	COUNT(skip) skips
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists on songs.artist=artists.id
WHERE
	user = ?
    AND songs.artist = ?
	AND skip = 1
GROUP BY
	song
ORDER BY
	skips DESC;

-- Top Skipped Songs with artist and date range
SELECT
	songs.artist,
	artists.name artist_name,
	songs.name,
	COUNT(skip) skips
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists on songs.artist=artists.id
WHERE
	user = ?
    AND songs.artist = ?
	AND skip = 1
    AND DATE(date) BETWEEN ? AND ?
GROUP BY
	song
ORDER BY
	skips DESC;
