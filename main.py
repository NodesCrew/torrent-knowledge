#!/usr/bin/env python3
# coding: utf-8

import os
import csv
import sys
import time
import json
from lib.log import logger
from lib.cli import parse_args
from lib.mask import MaskParser
from lib.mask import MaskTrainParser


EPISODE_PSEUDO_ID = "{series_id}-{season_no:02d}-{episode_no:02d}"


def read_test(name):
    with open("test/%s.json" % name) as f:
        return json.load(f).items()


def test_parser(parser):
    for test, expect in read_test("clean"):
        assert parser.clean_title(test) == expect, parser.clean_title(test)
        logger.debug("Test clean_title: '%s' -> '%s'", test, expect)

    for test, expect in read_test("mask"):
        assert parser.mask_title(test) == expect, parser.mask_title(test)
        logger.debug("Test mask_title: '%s' -> '%s'", test, expect)


def read_imdb_tv_shows(parser):
    tv_shows = dict()
    csv_path = "datasets/imdb_tv_shows.csv"
    logger.debug("Read IMDB TVShows dataset: %s", csv_path)

    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)
        for imdb_id, title in reader:
            title_clean = parser.clean_title(title)
            tv_shows[title_clean] = imdb_id

    logger.debug("Total IMDB TVShows dataset size: %s", len(tv_shows))
    return tv_shows


def read_imdb_tv_episodes(parser):
    tv_episodes = dict()
    csv_path = "datasets/imdb_tv_episodes.csv"
    logger.debug("Read IMDB TVEpisodes dataset: %s", csv_path)

    with open(csv_path) as csv_file:
        for line in csv_file:
            try:
                imdb_id, series_id, season_no, episode_no, title = line.strip().split(",", 4)
                title = title.strip('"\'')
            except:
                raise

            pseudo_id = EPISODE_PSEUDO_ID.format(
                series_id=series_id,
                season_no=int(season_no),
                episode_no=int(episode_no)
            )
            tv_episodes[pseudo_id] = imdb_id

    logger.debug("Total IMDB TVEpisodes dataset size: %s", len(tv_episodes))
    return tv_episodes


def parse_torrents(parser, tv_shows, tv_episodes):
    t0 = time.time()
    csv_path = "datasets/torrents_titles.csv"
    logger.debug("Read and parse torrents dataset: %s", csv_path)

    total = 0
    tv200 = 0
    tv404 = 0
    ep404 = 0
    ep200 = 0
    success_ids = set()

    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)
        for line in reader:
            total += 1
            if not total % 5000:
                logger.debug(
                    "Read Lines per second: %d, "
                    "tv200: %05d, tv404: %05d, "
                    "ep200: %05d, ep404: %05d",
                    total / (time.time() - t0), tv200, tv404, ep200, ep404)

            try:
                torrent_id, torrent_title = line
                torrent_id = torrent_id.upper()
            except ValueError:
                continue

            if torrent_id in success_ids:
                # Do not parse another title for success parsed torrents
                continue

            if len(torrent_title) > 128:
                continue

            total += 1
            try:
                torrent = parser.parse_title(torrent_title)

                assert torrent
                if torrent["series_name"] not in tv_shows:
                    tv404 += 1
                    continue
                tv200 += 1

                series_name = torrent.pop("series_name")
                series_id = tv_shows[series_name]
                pseudo_id = EPISODE_PSEUDO_ID.format(
                    series_id=series_id,
                    season_no=int(torrent["season_no"]),
                    episode_no=int(torrent["episode_no"])
                )

                if pseudo_id not in tv_episodes:
                    ep404 += 1
                    continue
                ep200 += 1

                success_ids.add(torrent_id)
                torrent.update({
                    "imdb_id": tv_episodes[pseudo_id],
                    "series_id": series_id,
                    "torrent_id": torrent_id,
                })
                yield torrent
            except AssertionError:
                pass

    logger.debug("Read Lines per second: %0.4f", total / (time.time() - t0))


def read_known_tv_shows_cache(path):
    with open(path) as f:
        for line in f:
            torrent = ""


def main():
    try:
        args = parse_args(sys.argv)
        logger.setLevel(max(3 - args.verbose, 0) * 10)

        parser_class = MaskParser

        if args.train_mode:
            logger.debug("Enable train mode")
            parser_class = MaskTrainParser

        parser = parser_class(
            train_mode=args.train_mode,
            chars_whitelist="[]{}&@#’%"
        )

        parser.create_regexps(
            year="(?P<year>19\d\d|20\d\d)",
            series_name="(?P<series_name>[\w\d\s]*?[\w\d])",
            episode_name="(?P<episode_name>.*?)",
            season_no="(?P<season_no>\d{1,2})",
            episode_no="(?P<episode_no>\d{1,2})"
        )

        logger.debug("Test parser via test/*.json")
        test_parser(parser)

        tv_shows = read_imdb_tv_shows(parser)
        tv_episodes = read_imdb_tv_episodes(parser)
        found_tv_shows = 0

        cache_path = "/tmp/torrents.json"
        if not os.path.exists(cache_path):
            t0 = time.time()
            with open(cache_path, "w+") as f:
                for torrent in parse_torrents(parser, tv_shows, tv_episodes):
                    f.write("{}\n".format(json.dumps(torrent)))
                    found_tv_shows += 1

                    if not found_tv_shows % 1000:
                        logger.debug("TVSeries torrents found: %s",
                                     found_tv_shows)

                        # if not found_tv_shows % 1000:
                        #    break
            logger.debug("Complete in %0.2f", time.time() - t0)

        if args.train_mode:
            parser.update_stats()

    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
    finally:
        import logging
        logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())
