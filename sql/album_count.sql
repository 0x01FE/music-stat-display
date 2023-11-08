-- Get Album Count
SELECT
	COUNT(DISTINCT songs.album) album_count
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	"listen-events".user = ?;

-- Get Album Count with date range
SELECT
	COUNT(DISTINCT songs.album) album_count
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
WHERE
	"listen-events".user = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?;