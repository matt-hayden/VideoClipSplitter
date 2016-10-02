#! /usr/bin/env python3
import argparse
import os, os.path
import subprocess
import sys

from . import *

from .AsfBin import AsfBinConverter, probe as AsfBin_probe
from .AviDemux import AviDemuxConverter, probe as AviDemux_probe
from .FFmpeg import FFmpegConverter, probe as FFmpeg_probe
from .gpac import GpacConverter, probe as Gpac_probe
from .MkvMerge import MkvMergeConverter, probe as MkvMerge_probe

from .m3u import *			# VLC extended m3u file produced by Clipper.lua
from .cutlist import *		# intermediate Windows format
from .splits_tsv import *	# user-defined tab-separated file

import logging
logger = logging.getLogger('' if __name__ == '__main__' else __name__)
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical

def get_argparser():
	ap = argparse.ArgumentParser(description="Transcode or convert a video from a list of segments")
	newarg = ap.add_mutually_exclusive_group().add_argument
	newarg('--quiet', '-q', action='store_const', dest='logging_level', const=logging.ERROR)
	newarg('--verbose', '-v', action='store_const', dest='logging_level', const=logging.INFO)
	newarg = ap.add_argument_group('general options').add_argument
	newarg('--converters', '-C', help="Comma-seperated list of programs, tried in order")
	newarg('--dry-run', '-n', action='store_true', help="Only show commands, do not run them")
	newarg('--output', '-o', help="Write to filename (instead of automatic)")
	newarg('files', nargs=2, help='2 files to parse')
	return ap


def get_probes(*args, **kwargs):
	probes = []
	y = probes.append
	if MkvMergeConverter.match_filenames(*args):
		y( ('mkvmerge', MkvMerge_probe) )
	if GpacConverter.match_filenames(*args):
		y( ('MP4Box', Gpac_probe) )
	if FFmpegConverter.match_filenames(*args):
		y( ('ffmpeg', FFmpeg_probe) )
	#if AviDemuxConverter.match_filenames(*args):
	#	y( ('avidemux', AviDemux_probe) )
	if AsfBinConverter.match_filenames(*args):
		y( ('asfbin', AsfBin_probe) )
	return probes
def get_converters(*args, **kwargs):
	converters = []
	y = converters.append
	if MkvMergeConverter.match_filenames(*args):
		y( ('mkvmerge', MkvMergeConverter(**kwargs)) )
	if GpacConverter.match_filenames(*args):
		y( ('MP4Box', GpacConverter(**kwargs)) )
	if FFmpegConverter.match_filenames(*args):
		y( ('ffmpeg', FFmpegConverter(**kwargs)) )
	if AviDemuxConverter.match_filenames(*args):
		y( ('avidemux', AviDemuxConverter(**kwargs)) )
	if AsfBinConverter.match_filenames(*args):
		y( ('asfbin', AsfBinConverter(**kwargs)) )
	return converters
def main(*args):
	if args:
		options_in = get_argparser().parse_args(args) # returns a Namespace
	else:
		options_in = get_argparser().parse_args()
	debug("Command-line in: {}".format(options_in))
	options_out = { 'dry_run': options_in.dry_run }
	if options_in.output:
		options_out['output_filename'] = options_in.output
	files = []
	#assert len(options_in.files) == 2
	for fn in options_in.files:
		if not os.path.isfile(fn):
			raise SplitterException("{} not found".format(fn))
		_, ext = os.path.splitext(fn)
		ext = ext.upper()
		if '.CUTLIST' == ext:
			options_out['splits'] = [ (cut.start, cut.end) for cut in cutlist(fn).cuts ]
			options_out['cut_units'] = 'seconds' # decimal
		elif '.M3U' == ext:
			options_out['splits'] = [ (cut.start, cut.end) for cut in extended_m3u_file(fn) ]
			options_out['cut_units'] = 'seconds' # decimal
		elif '.SPLITS' == ext:
			options_out['frames'] = old_splits_file(fn).cuts
			options_out['cut_units'] = 'frames'
		else:
			files.append(fn)
	debug("Command-line out: {}".format(options_out))
	if options_in.converters:
		cs = []
		y = cs.append
		for text in options_in.converters.split(','):
			cname = text.strip().upper()
			if 'MKVMERGE' == cname:
				y( ('mkvmerge', MkvMergeConverter(**options_out)) )
			elif 'MP4BOX' == cname:
				y( ('MP4Box', GpacConverter(**options_out)) )
			elif 'FFMPEG' == cname:
				y( ('ffmpeg', FFmpegConverter(**options_out)) )
			elif 'AVIDEMUX' == cname:
				y( ('avidemux', AviDemuxConverter(**options_out)) )
			elif 'ASFBIN' == cname:
				y( ('asfbin', AsfBinConverter(**options_out)) )
	else:
		cs = get_converters(*files, **options_out)
	debug( "{} possible converters:".format(len(cs)) )
	for cname, cobj in cs:
		debug( "{} at {}".format(cname, cobj.executable) )
	for cname, cobj in cs:
		info( "Running converter "+cname )
		successes = total = 0
		for success, log in cobj.run(*files, **options_out):
			# this section won't run during dry_run
			total += 1
			if success:
				successes += 1
			else:
				error( cname+" failed" )
				break
		else:
			break
		info( "{}/{} completed".format(successes, total) )
	else:
		panic( "All converters tried unsuccessfully" )
		return -1
def probe(*args, **kwargs):
	files = args
	ps = get_probes(*files, **kwargs)
	assert ps
	debug( "{} probes:".format(len(ps)) )
	for cname, f in ps:
		debug( "{} at {}".format(cname, f) )
	for cname, f in ps:
		result=("Pass" if f(*files) else "Fail")
		print("{}:\t{}".format(cname, result))

