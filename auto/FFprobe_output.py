#!/usr/bin/env python3
from collections  import defaultdict
from decimal import Decimal

#
def Tree(): return defaultdict(Tree)
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
		if key in ['lavfi_black_start', 'lavfi_black_end', 'tag:lavfi.scene_score']:
			tree[key] = Decimal(leaf_value)
		else:
			tree[key] = leaf_value
#
def parse(iterable):
	result = Tree()
	for line in iterable:
		tpath, value = line.rstrip().split('=', 1)
		add(result, tpath.split('.'), value)
	return result
		
if __name__ == '__main__':
	import pprint
	import sys
	with open(sys.argv[1]) as fi:
		r = parse(fi)
	pprint.pprint(r)
