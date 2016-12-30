# coding: utf-8
import sys
import logging

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)

logger = logging.getLogger()
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
