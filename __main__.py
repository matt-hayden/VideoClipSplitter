#!/usr/bin/env python3
"""Transcode or convert a video from a list of segments
  Usage:
    Splitter [options] [--] FILES...

  Options:
    -h --help  show this help message and exit
    --version  show version and exit
    -c, --converters=STRINGS  Comma-separated list of preferred tool(s)
    -f, --overwrite  Overwrite on output
    -n, --dry-run  Stop short of running converters
    -s, --separate  Each cut will be a separate file [default]

"""
import sys

import docopt

from . import *
from .cli import main

kwargs = docopt.docopt(__doc__, version=__version__) # make sure to pop 'FILES' out as file arguments
args = kwargs.pop('FILES')
sys.exit(main(*args, **kwargs))
