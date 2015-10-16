#!/usr/bin/env python3
import os, os.path
import time

from . import *

debug("Loading modules...")
from .converters import *	# harnesses for (external) converters
from .m3u import *			# VLC extended m3u file produced by Clipper.lua
from .cutlist import *		# intermediate Windows format
from .splits_tsv import *	# user-defined tab-separated file

###
def lookup(text_name):
	if text_name in ('asfbin', 'AsfBin'):
		return asfbin
	elif text_name in ('avidemux', 'AviDemux'):
		return avidemux
	elif text_name in ('ffmpeg', 'FFmpeg'):
		return ffmpeg
	elif text_name in ('mkvmerge', 'MkvMerge'):
		return mkvmerge
	elif text_name in ('mp4box', 'MP4Box'):
		return MP4Box
def get_converters(*args, **kwargs):
	if not args:
		return [], kwargs
	video_file = cuts = cut_units = '' # wouldn't do that with a classier object
	for arg in args:
		_, ext = os.path.splitext(arg)
		ext = ext.upper()
		if '.M3U' == ext:
			cuts, cut_units = [ (cut.start, cut.end) for cut in extended_m3u_file(arg) ], 'seconds' # decimal
		elif '.CUTLIST' == ext:
			cuts, cut_units = [ (cut.start, cut.end) for cut in cutlist(arg).cuts ], 'seconds' # decimal
		elif '.SPLITS' == ext:
			cuts, cut_units = old_splits_file(arg).cuts, 'frames'
		elif ext in ('.GIF', '.OGV'):
			video_file, converters = arg, [ffmpeg]
		elif ext in ('.AVI', '.DIVX'):
			video_file, converters = arg, [avidemux, ffmpeg]
		elif ext in ('.MKV', '.WEBM', '.FLV'):
			video_file, converters = arg, [mkvmerge, ffmpeg, avidemux]
		elif ext in ('.MPG', '.MP4', '.M4V', '.MOV', '.F4V', '.3GP', '.3G2', '.MJ2'):
			video_file, converters = arg, [MP4Box, mkvmerge, ffmpeg]
		elif ext in ('.ASF', '.WMV'):
			video_file, converters = arg, [asfbin, ffmpeg]
		else:
			raise SplitterException("{} not supported".format(arg))
		if any(f in kwargs for f in [ 'filters', 'audio_filters', 'video_filters' ] ):
			[ converters.remove(c) for c in [asfbin, mkvmerge, MP4Box] if c in converters ]
	if 'converters' in kwargs:
		info("Replacing default converters {}".format(converters))
		converters = [ lookup(t) for t in kwargs.pop('converters') ]
		info("with {}".format(converters))
	nargs = {}
	# can be overwritten within kwargs:
	nargs['video_file'] = video_file
	# this section defines 'seconds' as the default 'splits'
	if 'seconds' == cut_units: 
		nargs['splits'] = cuts
	else:
		nargs[cut_units] = cuts
	#
	nargs.update(kwargs) # what's left is passed through
	# ... so these are never overridden by kwargs:
	#nargs['profile'] = converters[0].__name__
	#
	return converters, nargs

def main(*args, **kwargs):
	debug("Arguments:")
	for arg in args:
		debug("\t{}".format(arg))
	### hacky:
	if 'converters' not in kwargs:
		if '--converters' in kwargs:
			kwargs['converters'] = kwargs.pop('--converters').split(',')
	###
	converters, kwargs = get_converters(*args, **kwargs)
	#if 'converter' in kwargs:
	#	converters = [kwargs.pop('converter')]
	#elif 'converters' in kwargs:
	#	converters = kwargs.pop('converters')
	if not converters:
		panic("No files in {} supported".format(args))
		return -1
	video_file = kwargs.pop('video_file')
	size = os.path.getsize(video_file)
	debug("{} is {:,} B".format(video_file, size))
	debug("Parameters:")
	for k, v in kwargs.items():
		debug("\t{}={}".format(k, v))
	st, dur = time.time(), 0.
	for is_retry, c in enumerate(converters):
		name, options = c.__name__, dict(kwargs) # kwargs can be modified by converter methods
		if not is_retry:
			info("Trying {}...".format(name))
		else:
			warning("Retry {} ({})...".format(is_retry, name))
			options['ext'] = '.MKV'
		st = time.time() # reset
		try:
			rc = c(video_file, dry_run=options['--dry-run'], **options)
		except OSError as e:
			panic("{} not found: {}".format(name, e))
			return -2
		except SplitterException as e:
			error("{} failed: {}".format(name, e))
		else:
			break
	else: # break not reached
		panic("No converters left")
		return -3
	dur = time.time() - st
	if size and dur:
		info("Processing took {:.1f} seconds at {:,.1f} MB/s".format(dur, size/10E6/dur))
	return 0
#
