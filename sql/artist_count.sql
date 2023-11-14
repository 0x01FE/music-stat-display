-- Get Artist Count
SELECT
	COUNT(DISTINCT songs.artist) artist_count
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	"listen-events".user = ?;

-- Get Artist Count with date range
SELECT
	COUNT(DISTINCT songs.artist) artist_count
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	"listen-events".user = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?;