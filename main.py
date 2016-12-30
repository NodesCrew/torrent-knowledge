# coding: utf-8
import os
import csv
import sys
import time
import json
from lib.log import logger
from lib.cli import parse_args
from lib.mask import MaskParser


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


def parse_torrents(parser, tv_shows):
    csv_path = "datasets/torrents_titles.csv"
    logger.debug("Read and parse torrents dataset: %s", csv_path)

    total = 0
    success_ids = set()

    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)
        for line in reader:
            try:
                torrent_id, torrent_title = line
                torrent_id = torrent_id.upper()
            except ValueError:
                continue

            if torrent_id in success_ids:
                # Do not parse another title for success parsed torrents
                continue

            total += 1
            try:
                torrent = parser.parse_title(torrent_title)

                assert torrent
                assert torrent["series_name"] in tv_shows

                success_ids.add(torrent_id)

                torrent["torrent_id"] = torrent_id
                yield torrent
            except AssertionError:
                pass


def read_known_tv_shows_cache(path):
    with open(path) as f:
        for line in f:
            torrent = ""

def main():
    try:
        args = parse_args(sys.argv)
        logger.setLevel(max(3 - args.verbose, 0) * 10)

        parser = MaskParser(
            train_mode=args.train_mode,
            chars_whitelist="[]{}&@#’%"
        )
        if args.train_mode:
            logger.debug("Enable train mode")

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
        found_tv_shows = 0

        cache_path = "/tmp/torrents.json"
        if not os.path.exists(cache_path):
            t0 = time.time()
            with open(cache_path, "w+") as f:
                for torrent in parse_torrents(parser, tv_shows):
                    f.write("{}\n".format(json.dumps(torrent)))
                    found_tv_shows += 1

                    if not found_tv_shows % 100:
                        logger.debug("TVSeries torrents found: %s",
                                     found_tv_shows)

                        if not found_tv_shows % 1000:
                            break
            logger.debug("Complete in %0.2f", time.time() - t0)
            for attr in parser.__slots__:
                if not attr.startswith("_"):
                    print(attr, getattr(parser, attr))

        if args.train_mode:
            parser.update_stats()

    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
    finally:
        import logging
        logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())