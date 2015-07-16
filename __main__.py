#!/usr/bin/env python3
import sys

#from . import *
from .cli import *

sys.exit(run(*sys.argv[1:]))
