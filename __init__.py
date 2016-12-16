#! /usr/bin/env python3

from datetime import datetime
import logging
import os
import shlex
import subprocess
import sys

import tqdm

__version__ = '0.2'
__all__ = [ '__version__' ]


if __name__ == '__main__':
	logger = logging.getLogger()
else:
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
		if not syntax:
			return
		debug( "Generated {} commands".format(len(syntax)) )
		if (not self.dry_run):
			for line in tqdm.tqdm(syntax, desc="{} arguments".format(len(syntax)), disable=not sys.stderr.isatty()):
				debug( " ".join(line) )
				proc = subprocess.Popen(line,
							stdin=subprocess.DEVNULL,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE)
				yield self.parse_output(proc.communicate(), returncode=proc.returncode)
		elif syntax:
			print('#! /usr/bin/env sh')
			for line in syntax:
				print(' '.join(shlex.quote(s) for s in line))
	def __repr__(self):
		return "<{}>".format(self.executable)
__all__ += ['ConverterBase']

