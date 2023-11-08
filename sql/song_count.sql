-- Get Song Count
SELECT
	COUNT(DISTINCT "listen-events".song) song_count
FROM
	"listen-events"
WHERE
	"listen-events".user = ?;

-- Get Song Count with date range
SELECT
	COUNT(DISTINCT "listen-events".song) song_count
FROM
	"listen-events"
WHERE
	"listen-events".user = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?;