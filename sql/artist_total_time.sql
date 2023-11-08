-- Get Total Time for Artist
SELECT
	SUM(time) time
FROM
	(SELECT
		SUM("listen-events".time) time
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	WHERE
		"listen-events".user = ?
		AND artists.name = ?
	GROUP BY
		"listen-events".song)
ORDER BY
	time DESC;

-- Get Total Time for Artist with date range
SELECT
	SUM(time) time
FROM
	(SELECT
		SUM("listen-events".time) time
	FROM
		"listen-events"
	INNER JOIN songs ON "listen-events".song=songs.id
	INNER JOIN artists ON songs.artist=artists.id
	WHERE
		"listen-events".user = ?
		AND artists.name = ?
        AND DATE("listen-events".date) BETWEEN ? AND ?
	GROUP BY
		"listen-events".song)
ORDER BY
	time DESC;