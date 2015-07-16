#!/usr/bin/env python3
import sys

__all__ = 'SplitterException debug warning error'.split()

output_stream = sys.stderr

if output_stream.isatty() or not __debug__:
	def debug(*args):
		pass
else:
	def debug(*args):
		print('debug:', *args, file=output_stream)
def error(*args):
	print(*args, file=output_stream)
warning=error

class SplitterException(Exception):
	pass
