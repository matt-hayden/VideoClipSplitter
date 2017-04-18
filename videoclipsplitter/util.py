#!/usr/bin/env python3
from pprint import pformat

class TinyPyException(Exception):
	pass
#
def wrap(*args, **kwargs):
	'''return lines that form a repr() suitable for TinyPy'''
	lines = pformat(*args, **kwargs).splitlines()
	if any(255 < len(_) for _ in lines):
		raise TinyPyException("Line limit 255 reached")
	for n, line in enumerate(lines, start=1-len(lines)):
		yield line+'\\' if n else line
#
def avoid_duplicates(iterable, prev=hash(''), n=0, encoding='UTF-8'):
	for line in iterable:
		this = hash(line)
		if this == prev:
			n += 1
		else:
			if 1 < n:
				yield "(Last message repeats {} more times)".format(n-1).encode(encoding)
				yield line
			else:
				yield line
			n = 1
		prev = this
	if prev: # exists when last line wasn't empty
		yield line
#
def flatten(iterable):
	for item in iterable:
		if isinstance(item, str):
			yield item
		elif hasattr(item, '__next__') or hasattr(item, '__iter__'):
			yield from item
		else:
			yield item
