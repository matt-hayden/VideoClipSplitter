#!/usr/bin/env python3
import os, os.path
import time

from . import *

debug("Loading modules")
from .converters import *
from .m3u import *
from .splits_tsv import *

###
def get_converter(*args, **kwargs):
	if not args:
		return None, kwargs
	video_file = cuts = cut_units = '' # wouldn't do that with a class
	for arg in args:
		_, ext = os.path.splitext(arg)
		ext = ext.upper()
		if '.M3U' == ext:
			cuts, cut_units = [ (cut.start, cut.end) for cut in extended_m3u_file(arg) ], 'seconds'
		elif '.SPLITS' == ext:
			cuts, cut_units = old_splits_file(arg).cuts, 'frames'
		elif ext in ('.AVI', '.DIVX'):
			video_file, converter = arg, avidemux
		elif ext in ('.MKV', '.WEBM', '.FLV'):
			video_file, converter = arg, mkvmerge
		elif ext in ('.MPG', '.MP4', '.MOV'):
			video_file, converter = arg, MP4Box
		elif ext in ('.ASF', '.WMV'):
			video_file, converter = arg, asfbin
		else:
			raise SplitterException(ext+" not supported")
	nargs = {}
	# can be overwritten:
	nargs['video_file'] = video_file
	# this section defines 'seconds' as the default 'splits'
	if 'seconds' == cut_units: 
		nargs['splits'] = cuts
	else:
		nargs[cut_units] = cuts
	#
	nargs.update(kwargs)
	# cannot be overwritten:
	nargs['profile'] = converter.__name__
	#
	return converter, nargs

def run(*args, **kwargs):
	converter, kwargs = get_converter(*args)
	if not converter:
		panic("No files "+", ".join("'{}'".format(a) for a in args)+" supported")
		return -3 # top of return codes
	video_file = kwargs.pop('video_file')
	size = os.path.getsize(video_file)
	debug("{} is {:,} B".format(video_file, size))
	debug("Parameters:")
	for k, v in kwargs.items():
		debug("\t{}={}".format(k, v))
	rc = -2
	st, dur = time.time(), 0.
	try:
		rc = converter(video_file, **kwargs)
	except OSError as e:
		panic("{} not found: {}".format(kwargs['profile'], e))
		return -1
	except SplitterException as e:
		error("{} failed: {}".format(kwargs.pop('profile'), e))
		st = time.time() # reset
		info("Trying fallback {}...".format(default_converter.__name__ or 'converter'))
		rc = default_converter(video_file, **kwargs)
	#except:
	#	raise
	#finally: # this block makes many exits very quiet
	#	return rc
	dur = time.time() - st
	if size and dur:
		info("Processing took {:.1f} seconds at {:,.1f} MB/s".format(dur, 10**-6*size/dur))
	return rc
#
