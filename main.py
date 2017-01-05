#!/usr/bin/env python3
# coding: utf-8

import os
import csv
import sys
import time
import json
import datetime
import collections
from lib.log import logger
from lib.cli import parse_args
from lib.mask import MaskParser
from lib.mask import MaskTrainParser

csv.field_size_limit(sys.maxsize)


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


def read_imdb_tv_series(parser):
    tv_series = dict()
    for file_name in ["imdb_tv_series.csv", "imdb_tv_series_extra.csv"]:
        csv_path = "datasets/%s" % file_name
        logger.debug("TVSeries dataset path: %s", csv_path)
        with open(csv_path) as csv_file:
            reader = csv.reader(csv_file, delimiter="|")
            next(reader)
            for imdb_id, title in reader:
                title_clean = parser.clean_title(title)
                tv_series[title_clean] = imdb_id

    logger.debug("TVSeries dataset size: %s", len(tv_series))
    return tv_series


def read_imdb_tv_episodes(parser):
    tv_episodes = dict()
    csv_path = "datasets/imdb_tv_episodes.csv"
    logger.debug("TVEpisodes dataset path: %s", csv_path)

    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file, delimiter="|")
        next(reader)
        for imdb_id, series_id, season_no, episode_no, title in reader:
            pseudo_id = EPISODE_PSEUDO_ID.format(
                series_id=series_id,
                season_no=int(season_no),
                episode_no=int(episode_no)
            )
            tv_episodes[pseudo_id] = imdb_id

    logger.debug("TVEpisodes dataset size: %s", len(tv_episodes))
    return tv_episodes


def parse_torrents(args, parser, tv_series, tv_episodes):

    def handle_tv_episode(_torrent):
        try:
            _torrent["season_no"] = int(_torrent["season_no"])
            _torrent["episode_no"] = int(_torrent["episode_no"])

            _pseudo_id = EPISODE_PSEUDO_ID.format(
                series_id=_torrent["series_id"],
                season_no=_torrent["season_no"],
                episode_no=_torrent["episode_no"]
            )
        except KeyError:
            return _torrent

        if _pseudo_id in tv_episodes:
            _torrent["imdb_id"] = tv_episodes[_pseudo_id]
            ep200[_pseudo_id] += 1
        else:
            ep404[_pseudo_id] += 1

        return _torrent

    def handle_tv_series(_torrent):
        _series_name = _torrent.pop("series_name")
        if _series_name not in tv_series:
            tv404[_series_name] += 1
            return _torrent

        _series_id = tv_series[_series_name]
        _torrent["series_id"] = _series_id
        tv200[_series_id] += 1

        _torrent = handle_tv_episode(_torrent)
        return _torrent

    t0 = time.time()
    logger.debug("Read and parse torrents dataset: %s", args.input_file.name)

    total = 0
    tv200 = collections.Counter()
    tv404 = collections.Counter()
    ep200 = collections.Counter()
    ep404 = collections.Counter()
    success_ids = set()

    reader = csv.reader(args.input_file, delimiter="|")

    for line in reader:
        total += 1
        if not total % 20000:
            logger.debug(
                "Complete: %8d, "
                "lines/sec: %5d, "
                "tv200: %05d, tv404: %05d, "
                "ep200: %05d, ep404: %05d",
                total,
                int(total / (time.time() - t0)),
                len(tv200),
                len(tv404),
                len(ep200),
                len(ep404)
            )
            if not total % 100000:
                break

        try:
            torrent_id, torrent_title = line
            assert len(torrent_id) == 40
            assert 3 < len(torrent_title) < 128
            torrent_id = torrent_id.upper()
            assert all(ch in "01234567890ABCDEF" for ch in torrent_id)
            assert torrent_id not in success_ids
        except (AssertionError, ValueError):
            continue

        try:
            torrent = parser.parse_title(torrent_title)
            assert torrent

            torrent["torrent_id"] = torrent_id

            if "series_name" in torrent:
                torrent = handle_tv_series(torrent)
                success_ids.add(torrent_id)

            yield torrent
        except AssertionError:
            pass

    logger.debug(
        "Complete: %8d, "
        "lines/sec: %5d, "
        "tv200: %05d, tv404: %05d, "
        "ep200: %05d, ep404: %05d",
        total,
        int(total / (time.time() - t0)),
        len(tv200),
        len(tv404),
        len(ep200),
        len(ep404)
    )

    if args.log_dir:
        dir_path = "%s/%s-%s" % (
            args.log_dir.rstrip(),
            datetime.datetime.utcnow().isoformat(),
            total
        )

        try:
            os.makedirs(dir_path)
        except FileExistsError:
            raise

        def write_with_freq(name, counter):
            with open(os.path.join(dir_path, "%s.txt" % name), "w+") as csv_path:
                writer = csv.writer(csv_path, delimiter="|")
                for row in sorted(counter.items(), key=lambda x: x[1], reverse=True):
                    writer.writerow(row[::-1])

        if ep200:
            write_with_freq("ep200", ep200)
        if ep404:
            write_with_freq("ep404", ep404)
        if tv200:
            write_with_freq("tv200", tv200)
        if tv404:
            write_with_freq("tv404", tv404)


def main():
    try:
        args = parse_args(sys.argv)
        logger.setLevel(max(3 - args.verbose, 0) * 10)

        parser_class = MaskParser

        if args.train_mode:
            logger.debug("Enable train mode")
            parser_class = MaskTrainParser

        if args.log_dir:
            logger.debug("Enable statistics logging into %s", args.log_dir)

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

        tv_series = read_imdb_tv_series(parser)
        tv_episodes = read_imdb_tv_episodes(parser)

        output = args.output_file
        t0 = time.time()

        for torrent in parse_torrents(args, parser, tv_series, tv_episodes):
            output.write("{}\n".format(json.dumps(torrent)))

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
