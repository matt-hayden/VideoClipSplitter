#!/usr/bin/env python3
import os.path
import subprocess
import sys

from . import *
class FFmpegException(SplitterException):
	pass
debug("Loading modules...")
from .FFprobe import ffprobe as FFmpeg_probe

if sys.platform.startswith('win'):
	ffmpeg_executable = 'FFMPEG.EXE'
else:
	ffmpeg_executable = 'ffmpeg'
debug("FFmpeg is {}".format(ffmpeg_executable))

def FFmpeg_command(input_filename, output_filename=None, **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if 'ext' in kwargs:
		ext = kwargs.pop('ext').upper()
	if not output_filename:
		output_filename = filepart+'_Cut'+ext
	command = kwargs.pop('command', [])
	if 'title' in kwargs:
		command += [ '-metadata', 'title='+kwargs.pop('title') ]
	if 'cut' in kwargs:
		cut = kwargs.pop('cut')
		if not isinstance(cut, (list, tuple)):
			raise FFmpegException("{} not a valid (timestamp, timestamp) cut".format(cut))
		try:
			b, e = cut
			'''The order of ffmpeg -i command matters
			'''
			if kwargs.pop('fast', False):
				if b:
					command += [ '-ss', str(b) ]
				command += [ '-i', input_filename ]
			else:
				command += [ '-i', input_filename ]
				if b:
					command += [ '-ss', str(b) ]
			if e:
				command += [ '-to', str(e) ]
		except Exception as e:
			raise FFmpegException("{} not a valid (timestamp, timestamp) cut: {}".format(cut, e))
	if kwargs.pop('copy', True):
		if ext.upper() not in ['.ASF', '.WMV']:
			debug("Direct stream copy")
			command += [ '-c:v', 'copy', '-c:a', 'copy' ]
		else:
			info("Direct stream copy disabled for {} format".format(ext))
	command += [ output_filename ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ffmpeg_executable]+command
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
		for b in errs.splitlines():
			_parse(b, prefix='STDERR')
	#for b in outs.splitlines(): # FFmpeg doesn't believe in stdout
	#	_parse(b)
	return returncode or 0
def ffmpeg(input_filename, **kwargs):
	def _run(command, **kwargs):
		debug("Running {}".format(command))
		proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # stdin redirected because of lack of ffmpeg feature
		out, err = proc.communicate()
		return parse_output(out, err, proc.returncode)
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		error("Failed to open '{}'".format(input_filename))
		return -1
	if 'ext' in kwargs:
		ext = kwargs.pop('ext').upper()
	output_file_pattern = kwargs.pop('output_file_pattern', filepart+'-{:03d}'+ext)
	debug("Running probe...")
	p = FFmpeg_probe(input_filename)
	if not p:
		raise FFmpegException("Failed to open '{}'".format(input_filename))
	if 'frames' in kwargs:
		debug("Converting frames")
		kwargs['splits'] = [ (int(b)/fps if b else '', int(e)/fps if e else '') for (b, e) in kwargs.pop('frames') ]
	if 'splits' in kwargs:
		splits = kwargs.pop('splits')
		debug("Running {} commands".format(len(splits)) )
		errors = 0
		for n, (b, e) in enumerate(splits, start=1):
			ofn = output_file_pattern.format(n)
			if not _run(FFmpeg_command(input_filename, output_filename=ofn, cut=(b,e), **kwargs)):
				debug("part {} succeeded".format(n))
			else:
				error("part {} failed".format(n))
				errors += 1
		return 0 if errors else -2
	else:
		return _run(FFmpeg_command(input_filename, **kwargs))
