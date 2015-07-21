#!/usr/bin/env python3
import sys

from . import *
from .cli import *

debug(sys.executable+" "+sys.version+" on "+sys.platform)
sys.exit(run(*sys.argv[1:]))
