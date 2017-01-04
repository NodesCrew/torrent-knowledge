CMD_PREFIX="psql -h localhost -S torrents -d torrents -A -c \"COPY ";
CMD_SUFFIX="TO STDOUT DELIMITER '|' CSV HEADER;\"";

cd datasets;
wc -l imdb_tv_series.csv;
time ssh -C sys_1 "$CMD_PREFIX (select imdb_id, title from imdb_tv_series) $CMD_SUFFIX" | sort > imdb_tv_series.csv;
wc -l imdb_tv_series.csv;


wc -l imdb_tv_episodes.csv;
time ssh -C sys_1 "$CMD_PREFIX (select imdb_id, series_id, season_no, episode_no, title from imdb_tv_episodes) $CMD_SUFFIX" | sort > imdb_tv_episodes.csv;
wc -l imdb_tv_episodes.csv;


wc -l imdb_movies.csv;
time ssh -C sys_1 "$CMD_PREFIX (select imdb_id, title from imdb_movies) $CMD_SUFFIX" | sort > imdb_movies.csv;
wc -l imdb_movies.csv;


wc -l torrents.csv;
time ssh -C sys_1 "$CMD_PREFIX (select distinct on (torrent_id, title) torrent_id, title from torrents_pubs) $CMD_SUFFIX" | grep "|" | sort -u > torrents.csv;
wc -l torrents.csv;


# root@ns535588:/home/workers/bth-server/data/imdbpie# find title_plots/ -iname "*.json" | wc -l
# 749146

# Sun Jan  1 19:31:14 UTC 2017
# 750008

# Sun Jan  1 21:32:51 UTC 2017
# 752044

# Sun Jan  1 22:54:08 UTC 2017
# 753730

# Mon Jan  2 07:16:21 UTC 2017
# 766990

# Mon Jan  2 09:44:50 UTC 2017
# 770963

# Mon Jan  2 12:34:53 UTC 2017
# 775427

# Mon Jan  2 22:45:55 UTC 2017
# 795275
