SELECT
	artists.name
FROM
	songs
INNER JOIN artists on songs.artist=artists.id
WHERE
	songs.id = ?;
