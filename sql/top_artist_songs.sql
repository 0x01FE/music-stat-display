-- Get Top Songs for Artist
SELECT
	artists.name artist_name,
	songs.name song_name,
	SUM("listen-events".time) time,
	COUNT(songs.name) play_count
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	"listen-events".user = ?
	AND artists.name = ?
GROUP BY
	song_name
ORDER BY
	time DESC;

-- Get Top Songs for Artist with date range
SELECT
	artists.name artist_name,
	songs.name song_name,
	SUM("listen-events".time) time,
	COUNT(songs.name) play_count
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	"listen-events".user = ?
	AND artists.name = ?
    AND DATE("listen-events".date) BETWEEN ? AND ?
GROUP BY
	song_name
ORDER BY
	time DESC;
