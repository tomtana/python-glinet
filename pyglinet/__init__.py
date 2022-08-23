"""
python-pyglinet json-rpc api client

"""
__author__ = 'Thomas Fontana'

from pyglinet.glinet import GlInet
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")