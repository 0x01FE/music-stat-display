DROP TABLE if exists f; -- Delete the temp table if it exists
CREATE TEMP TABLE f(artist_name TEXT, artist_spotify_id TEXT, song_name TEXT, song_spotify_id TEXT, plays INTEGER);

-- Throw subquery into temp table (because we need to select from it for the MAX plays value)
INSERT INTO f
SELECT
	artists.name,
	artists.spotify_id artist_spotify_id,
	songs.name,
	songs.spotify_id song_spotify_id,
	COUNT(song) / COUNT (DISTINCT songs.artist) plays
FROM
	"listen-events"
INNER JOIN songs ON "listen-events".song=songs.id
INNER JOIN artists ON songs.artist=artists.id
WHERE
	user = ?
	AND DATE("listen-events".date) BETWEEN ? AND ?
GROUP BY
	songs.id
ORDER BY
	plays DESC;


-- Get the output
SELECT
	*,
	CASE
		WHEN plays > ((SELECT MAX(plays) FROM f) * 0.75) THEN 1.0
		ELSE ((plays * 1.0) / (SELECT MAX(plays) FROM f)) + 0.1
		END weight
FROM
	f
GROUP BY
	song_spotify_id
ORDER BY
	weight DESC
LIMIT ?
OFFSET ?;
