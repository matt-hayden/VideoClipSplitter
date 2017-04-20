
from datetime import datetime
import logging
import os
import shlex
import subprocess
import sys


logger = logging.getLogger('' if __name__ == '__main__' else __name__)
debug, info, warning, error, fatal = logger.debug, logger.info, logger.warning, logger.error, logger.critical

if sys.stderr.isatty():
	import tqdm
	progress_bar = tqdm.tqdm
else:
	def progress_bar(iterable, **kwargs):
		return iterable


class SplitterException(Exception):
	pass


filename_encoding = stream_encoding = 'UTF-8' # this is overridden on a per-method or per-module basis


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
			for line in progress_bar(syntax, desc="{} arguments".format(len(syntax)), disable=not sys.stderr.isatty()):
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

