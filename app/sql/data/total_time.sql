-- Get Total Listen Time For User
SELECT
	SUM(time) time
FROM
	(SELECT
		SUM("listen-events".time) time
	FROM
		"listen-events"
	WHERE
		"listen-events".user = ?
	GROUP BY
		"listen-events".song)
ORDER BY
	time DESC;

-- Get Total Listen Time For User with date range
SELECT
	SUM(time) time
FROM
	(SELECT
		SUM("listen-events".time) time
	FROM
		"listen-events"
	WHERE
		"listen-events".user = ?
        AND DATE("listen-events".date) BETWEEN ? AND ?
	GROUP BY
		"listen-events".song)
ORDER BY
	time DESC;