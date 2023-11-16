-- Get Top Albums for Artist
SELECT
	artists.name artist_name,
	albums.name album_name,
	SUM("listen-events".time) time
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
INNER JOIN albums on songs.album=albums.id
WHERE
	"listen-events".user = ?
	AND artists.id = ?
GROUP BY
	album_name
ORDER BY
    time DESC;

-- Get Top Albums for Artist with date range
SELECT
	artists.name artist_name,
	albums.name album_name,
	SUM("listen-events".time) time
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
INNER JOIN albums on songs.album=albums.id
WHERE
	"listen-events".user = ?
	AND artists.id = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?
GROUP BY
	album_name
ORDER BY
    time DESC;
