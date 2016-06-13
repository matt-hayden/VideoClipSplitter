#! /usr/bin/env python3
import logging
import sys
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.WARNING)
from .cli import main
sys.exit(main(*sys.argv[1:]))
