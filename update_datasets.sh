CMD_PREFIX="psql -h localhost -S torrents -d torrents -A -c \"COPY ";
CMD_SUFFIX="TO STDOUT DELIMITER '|' CSV HEADER;\"";

cd datasets;
wc -l imdb_tv_series.csv;
time ssh -C sys_1 "$CMD_PREFIX (select imdb_id, title from imdb_tv_series) $CMD_SUFFIX" > imdb_tv_series.csv;
wc -l imdb_tv_series.csv;


wc -l imdb_tv_episodes.csv;
time ssh -C sys_1 "$CMD_PREFIX (select imdb_id, series_id, season_no, episode_no, title from imdb_tv_episodes) $CMD_SUFFIX" > imdb_tv_episodes.csv;
wc -l imdb_tv_episodes.csv;


wc -l imdb_movies.csv;
time ssh -C sys_1 "$CMD_PREFIX (select imdb_id, title from imdb_movies) $CMD_SUFFIX" > imdb_movies.csv;
wc -l imdb_movies.csv;


wc -l torrents.csv;
time ssh -C sys_1 "$CMD_PREFIX (select distinct on (torrent_id, title) torrent_id, title from torrents_pubs) $CMD_SUFFIX" > torrents.csv;
wc -l torrents.csv;
