#!/usr/bin/env python3
import logging
import sys

import tqdm

__version__ = '0.1'
__all__ = [ '__version__' ]


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.WARNING)
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical
### __all__.extend('debug warning info error panic'.split()) ###


class SplitterException(Exception):
	pass
__all__ += ['SplitterException']


filename_encoding = stream_encoding = 'UTF-8' # this is overridden on a per-method or per-module basis
__all__.extend('filename_encoding stream_encoding'.split())


class ConverterBase:
	'''
	Subclasses should define .executable and implement get_commands() and parse_output()
	'''
	def run(self, *args, **kwargs):
		syntax = self.get_commands(*args, **kwargs)
		info( "Generated {} commands".format(len(syntax)) )
		if not self.dry_run:
			for line in tqdm.tqdm(syntax, disable=(len(syntax)<=1) or not sys.stdout.isatty()):
				debug( " ".join(line) )
				proc = subprocess.Popen(line,
							stdin=subprocess.DEVNULL,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE)
				yield self.parse_output(proc.communicate(), returncode=proc.returncode)
		else:
			for line in syntax:
				print(line)
	def __repr__(self):
		return "<{}>".format(self.executable)
__all__ += ['ConverterBase']


from .converters import *
__all__ += ['converters']
