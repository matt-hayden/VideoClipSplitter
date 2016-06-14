#! /usr/bin/env python3
import sys

from .cli import main
sys.exit(main(*sys.argv[1:]))
