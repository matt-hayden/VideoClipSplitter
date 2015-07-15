#!/usr/bin/env python3

def parse(rows, NonePlaceholder=None):
	last_end = NonePlaceholder
	for order, (start, label, end) in enumerate(rows):
		try:
			mystart = int(start)
		except:
			mystart = last_end
		try:
			myend = int(end) or NonePlaceholder
		except:
			myend = NonePlaceholder
		yield mystart, myend
		last_end = myend

class old_splits_file:
	def __init__(self, filename=None):
		if filename:
			self.open(filename)
	def open(self, filename=None, delim='\t'):
		self.filename = filename
		with open(filename, 'Ur') as fi:
			self.lines = [ line.rstrip('\n') for line in fi if line.strip() ]
		self.rows = [ line.split(delim) for line in self.lines ]
		#self.cuts = [ (b, e) for (b, label, e) in self.rows ]
		self.cuts = list(parse(self.rows))
