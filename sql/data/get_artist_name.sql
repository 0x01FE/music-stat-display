-- Get Artist Name by Id
SELECT DISTINCT
	artists.name
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	artists.id = ?;
