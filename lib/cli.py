# coding: utf-8

import sys
import argparse
from lib.log import logger


def parse_args(argv):
    """Parse command line argument. See -h option
    :param argv: arguments on the command line must include caller file name.
    """
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description="Run torrent-knowledge cli",
                                     formatter_class=formatter_class)

    parser.add_argument("-i", "--input_file",
                        type=argparse.FileType('r'),
                        required=True,
                        help="CSV with torrents in format 'info_hash|torrent_title'")

    parser.add_argument("-o", "--output_file",
                        required=True,
                        type=argparse.FileType('w'),
                        default=sys.stdout)

    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="count", default=0,
                        help="increase log verbosity via -vvv")

    parser.add_argument("-t", "--train-mode", dest="train_mode",
                        action="count", default=0,
                        help="update features frequency from dataset")

    parser.add_argument("-l", "--log-dir", dest="log_dir",
                        action="store", default=None,
                        help="directory for log files (only for -vvv mode)")

    args = parser.parse_args(argv[1:])

    if args.log_dir and args.verbose != 3:
        logger.debug("You should use -vvv with option -l")
        exit(-1)

    return parser.parse_args(argv[1:])