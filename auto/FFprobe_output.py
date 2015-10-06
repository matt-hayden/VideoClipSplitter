#!/usr/bin/env python3
import pprint

import collections
from decimal import Decimal

#
def Tree(): return collections.defaultdict(Tree)
class Frame(collections.namedtuple('Frame', 'frame timestamp')):
	@property
	def t(self):
		return self.timestamp
	def __int__(self):
		return int(self.frame or 0)
	def __float__(self):
		return float(self.timestamp or 0.0)
	def __sub__(self, other):
		return Frame(self.frame-other.frame, self.timestamp-other.timestamp)
	def get_fps(self):
		if self.timestamp:
			return round( (self.frame+1)/Decimal(self.timestamp), 2)
class BlackDetectCut(collections.namedtuple('BlackDetectCut', 'start end')):
	@staticmethod
	def from_frame_desc(p1, p2):
		f1, d1 = p1
		f2, d2 = p2
		dd1, dd2 = d1['tags'], d2['tags']
		[t1], [t2] = dd1.values(), dd2.values()
		return BlackDetectCut( Frame(f1, t1), Frame(f2, t2) )
def BlackDetectCutList(frames):
	assert not len(frames) % 2
	pairs = zip(frames[0::2], frames[1::2])
	return [ BlackDetectCut.from_frame_desc(*p) for p in pairs ]
#
def dequote(t, quote_chars='''"'`'''):
	if 2 < len(t):
		while t and (t[0] == t[-1]) and t[0] in quote_chars:
			t = t[1:-1]
	return t
def add(tree, path, leaf_value=None):
	key = path.pop(-1)
	leaf_value = dequote(leaf_value.strip())
	for node in path:
		if node.isdigit():
			node = int(node)
		tree = tree[node]
	if key:
		if leaf_value.isdigit():
			tree[key] = int(leaf_value)
		elif '.' in leaf_value:
			try:
				tree[key] = Decimal(leaf_value)
			except:
				tree[key] = leaf_value
		else:
			tree[key] = leaf_value
#
def parse_flat(iterable):
	result = Tree()
	for line in iterable:
		tpath, value = line.rstrip().split('=', 1)
		add(result, tpath.split('.'), value)
	return result
def parse(iterable):
	frame_dict = parse_flat(iterable)['frames']['frame']
	if not frame_dict:
		return {}
	frames = sorted(frame_dict.items())
	first_frame = frames[0]
	if 'lavfi_black_start' in first_frame[1]['tags']:
		#if float(first_frame.start) < 1/15.:
		if float(first_frame[0]) < 1/15.:
			frames.pop(0)
		if len(frames) <= 1:
			debug("Likely no black segments")
	if not frames:
		return {}
	cutlist = BlackDetectCutList(frames)
	_, last = cutlist[-1]
	return { 'fps': last.get_fps(), 'frames': cutlist }
#
def load(filename):
	with open(filename) as fi:
		return parse(fi)
if __name__ == '__main__':
	import pprint
	import sys
	bd=load(sys.argv[1])
	pprint.pprint(bd)
