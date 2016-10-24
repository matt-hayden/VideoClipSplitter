#! /usr/bin/env python3

from datetime import datetime
import logging
import shlex
import subprocess
import sys

if sys.stderr.isatty():
	import tqdm
	progress_bar = tqdm.tqdm
else:
	def progress_bar(iterable, **kwargs):
		return iterable

__version__ = '0.2'
__all__ = [ '__version__' ]


logger = logging.getLogger(__name__)
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
		syntax = list(self.get_commands(*args, **kwargs))
		debug( "Generated {} commands".format(len(syntax)) )
		if (not self.dry_run):
			for line in progress_bar(syntax):
				debug( " ".join(line) )
				proc = subprocess.Popen(line,
							stdin=subprocess.DEVNULL,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE)
				yield self.parse_output(proc.communicate(), returncode=proc.returncode)
		else:
			print('#! /usr/bin/env sh')
			for line in syntax:
				print(' '.join(shlex.quote(s) for s in line))
	def __repr__(self):
		return "<{}>".format(self.executable)
__all__ += ['ConverterBase']


debug( "Started at {}".format(datetime.now()) )
