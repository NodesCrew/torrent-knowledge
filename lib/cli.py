# coding: utf-8

import argparse
from lib.log import logger


def parse_args(argv):
    """Parse command line argument. See -h option
    :param argv: arguments on the command line must include caller file name.
    """
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description="Run torrent-knowledge cli",
                                     formatter_class=formatter_class)

    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="count", default=0,
                        help="increase log verbosity via -vvv")

    parser.add_argument("-t", "--train-mode", dest="train_mode",
                        action="count", default=0,
                        help="update features frequency from dataset")

    return parser.parse_args(argv[1:])