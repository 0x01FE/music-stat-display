SELECT
	song
FROM
	"listen-events"
WHERE
	user = ?
ORDER BY
	date DESC
LIMIT ?;
