#! /usr/bin/env python3

import collections
import os, os.path

import FFprobe_output

def form_m3u_entry(filename, start_time=-1, stop_time=-1, label=None, time_format='.3f'):
	if not label:
		dirname, basename = os.path.split(filename)
		filepart, ext = os.path.splitext(basename)
	if 0 < start_time:
		yield '#EXTVLCOPT:start-time={:{time_format}}'.format(start_time, time_format=time_format)
	if 0 < stop_time:
		yield '#EXTVLCOPT:stop-time={:{time_format}}'.format(stop_time, time_format=time_format)
	duration = stop_time-start_time
	yield '#EXTINF:{duration:{time_format}},{label}'.format(**locals())
	yield filename
def form_ClipperPlaylist(cuts):
	yield '#EXTM3U'
	for cut in cuts:
		yield ''
		yield from form_m3u_entry(*cut)
#
def convert(filename):
	blackdetect_filename = filename+'.blackdetect'
	bdinfo = FFprobe_output.load(blackdetect_filename)
	bdcuts = bdinfo['frames']
	cpcuts = [ (filename, start.t, stop.t, "Segment {}".format(n)) for n, (start, stop) in enumerate(bdcuts, start=1) ]
	for line in form_ClipperPlaylist(cpcuts):
		print(line)
#
if __name__ == '__main__':
	import sys
	convert(sys.argv[1])
