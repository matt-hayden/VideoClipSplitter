#!/usr/bin/env python3
import sys

from Splitter import debug, info, warning, error, panic
from Splitter.cli import run
from Splitter.MkvMerge import mkvmerge

debug(sys.executable+" "+sys.version+" on "+sys.platform)
run(*sys.argv[1:], converter=mkvmerge)
