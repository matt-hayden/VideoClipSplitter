#!/usr/bin/env python3
import os.path
import shlex
import subprocess
import sys

import tqdm

from . import *
from .util import *

class FFmpegException(SplitterException):
	pass

debug("Loading modules...")
from .FFprobe import ffprobe as FFmpeg_probe

if sys.platform.startswith('win'):
	ffmpeg_executable = 'FFMPEG.EXE'
else:
	ffmpeg_executable = 'ffmpeg'
debug("FFmpeg is {}".format(ffmpeg_executable))

def FFmpeg_command(input_source, output_filename_pattern='{filepart}-%03d{output_ext}', **kwargs):
	dirname, basename = os.path.split(input_source)
	filepart, ext = os.path.splitext(basename)
	output_ext = kwargs.pop('output_ext', ext.upper())
	filters = kwargs.pop('filters', [])
	### arguments could go here before input source
	command = [ '-i', input_source ]
	if 'title' in kwargs:
		command += [ '-metadata', 'title='+kwargs.pop('title') ]
	if 'frames' in kwargs:
		command += '-f segment -map 0 -flags +global_header'.split()
		frame_splits = sorted(set(f for f in flatten(kwargs.pop('frames')) if f)-set([0, '0']), key=float)
		command += [ '-segment_frames', ','.join(frame_splits) ]
	elif 'splits' in kwargs: # these are decimal times
		command += '-f segment -map 0 -flags +global_header'.split()
		time_splits = sorted(set(t for t in flatten(kwargs.pop('splits')) if t)-set([0, '0']), key=float)
		command += [ '-segment_times', ','.join(time_splits) ]
	if ext.upper() in ['.ASF', '.WMV']:
		info("Direct stream copy disabled")
		output_ext = '.NUT'
	elif not filters:
		command += [ '-c:v', 'copy', '-c:a', 'copy' ]
	command.extend(filters)
	try:
		ofn = output_filename_pattern.format(**locals())
	except:
		warning("Output filename is {}, which is probably not what you want".format(output_filename_pattern))
		ofn = output_filename_pattern
	command += [ ofn ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ffmpeg_executable, '-nostdin']+command
def parse_output(outs, errs='', returncode=None):
	warnings = [ 'deprecated pixel format used, make sure you did set range correctly',
				 'DTS discontinuity',
				 'Invalid timestamp',
				 'Non-increasing DTS',
				 'VBV buffer size not set, muxing may fail' ]
	def _parse(b, prefix='STDOUT', warnings=warnings, encoding=stream_encoding):
		lastframeline = ''
		line = b.decode(encoding).rstrip()
		if 'Unrecognized option' in line:
			raise FFmpegException(line)
		elif 'At least one output file must be specified' in line:
			raise FFmpegException(line)
		elif 'Error opening filters!' in line:
			raise FFmpegException(line)
		elif 'Output file is empty, nothing was encoded' in line:
			if lastframeline: error(lastframeline) #
			raise FFmpegException(line)
		elif 'Press [q] to stop, [?] for help' in line:
			warning('Running interactive (maybe try -nostdin if using ffmpeg later than the avconv fork)')
		elif line.startswith('frame='): # progress
			lastframeline = line
		else:
			for w in warnings:
				if w in line:
					warning(line)
					break
			else:
				debug(prefix+' '+line)
		return(lastframeline) # progress bar
	if errs:
		for b in avoid_duplicates(errs.splitlines()):
			_parse(b, prefix='STDERR')
	#for b in outs.splitlines(): # FFmpeg doesn't believe in stdout
	#	_parse(b)
	return returncode or 0
def ffmpeg(input_filename, dry_run=False, **kwargs):
	if not dry_run:
		def _dispatch(command):
			debug("Running "+' '.join(command))
			proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = proc.communicate()
			return parse_output(out, err, proc.returncode)
	else:
		def _dispatch(command):
			print(' '.join(shlex.quote(s) for s in command))
			return 0
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		raise FFmpegException("'{}' not found".format(input_filename))
	output_ext = kwargs.pop('output_ext', ext.upper())
	debug("Running probe...")
	if not FFmpeg_probe(input_filename):
		raise FFmpegException("Failed to open '{}'".format(input_filename))
	command = FFmpeg_command(input_filename, **kwargs)
	return not _dispatch(command)
