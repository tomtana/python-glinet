"""
python-pyglinet json-rpc api client

"""

__author__ = "Tomtana"

import logging
import sys

from pyglinet.glinet import GlInet

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
