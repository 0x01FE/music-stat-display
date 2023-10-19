-- Top Songs
SELECT
	artists.name artist_name,
	songs.name song_name,
	SUM("listen-events".time) time
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	"listen-events".user = ?
GROUP BY
	"listen-events".song,
	songs.artist
ORDER BY
	time DESC;

-- Top Songs with date range
SELECT
	artists.name artist_name,
	songs.name song_name,
	SUM("listen-events".time) time
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	"listen-events".user = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?
GROUP BY
	"listen-events".song,
	songs.artist
ORDER BY
	time DESC;
