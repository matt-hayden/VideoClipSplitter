#!/usr/bin/env python3
import logging
import sys

__version__ = '0.1'
__all__ = [ '__version__' ]


class SplitterException(Exception):
	pass
__all__ += ['SplitterException']


# basic logging:
logger = logging.getLogger(__name__) # always returns the same object
if __debug__:
	logging.basicConfig(level=logging.DEBUG)
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical
__all__.extend('debug warning info error panic'.split())


filename_encoding = stream_encoding = 'UTF-8' # this is overridden on a per-method or per-module basis
__all__.extend('filename_encoding stream_encoding'.split())

from .converters import *

__all__ += ['converters']
