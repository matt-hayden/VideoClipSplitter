#!/usr/bin/env python3
import logging
import sys

__all__ = 'SplitterException debug warning info error critical'.split()

# basic logging:
logger = logging.getLogger(__name__) # always returns the same object
if sys.stderr.isatty() or not __debug__:
	logging.basicConfig(level=logging.WARNING)
else:
	logging.basicConfig(level=logging.DEBUG)
debug, info, warning, error, critical = logger.debug, logger.info, logger.warning, logger.error, logger.critical

class SplitterException(Exception):
	pass
