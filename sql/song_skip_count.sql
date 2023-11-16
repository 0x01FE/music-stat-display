-- Song Skip Count
SELECT
	COUNT(skip) skips
FROM
	"listen-events"
WHERE
	user = ?
	AND song = ?
	AND skip = 1;

-- Song Skip Count with date range
SELECT
	COUNT(skip) skips
FROM
	"listen-events"
WHERE
	user = ?
	AND song = ?
	AND skip = 1
    AND DATE(date) BETWEEN ? AND ?;
