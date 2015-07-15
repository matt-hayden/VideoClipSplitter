import sys

class SplitterException(Exception):
	pass

if sys.stderr.isatty():
	def debug(*args):
		pass
else:
	def debug(*args):
		print('debug:', *args, file=sys.stderr)
def error(*args):
	print(*args, file=sys.stderr)
warning=error
