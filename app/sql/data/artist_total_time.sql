-- Get Total Time for Artist
SELECT
	SUM("listen-events".time) time
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	"listen-events".user = ?
	AND songs.artist = ?
GROUP BY
	"listen-events".song
	AND songs.artist;

-- Get Total Time for Artist with date range
SELECT
	SUM("listen-events".time) time
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	"listen-events".user = ?
	AND songs.artist = ?
	AND DATE("listen-events".date) BETWEEN ? AND ?
GROUP BY
	"listen-events".song
	AND songs.artist;
