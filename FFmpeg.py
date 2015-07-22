#!/usr/bin/env python3
from decimal import Decimal
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

def FFmpeg_command(input_filename, output_filename=None, fast=False, **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not output_filename:
		output_filename = filepart+'_Cut'+ext
	command = kwargs.pop('command', [])
	'''FFmpeg takes (timestamp, duration) instead of (timestamp, timestamp)
	'''
	if 'cut' in kwargs:
		cut = kwargs.pop('cut')
		if not isinstance(cut, (list, tuple)):
			raise FFmpegException("{} not a valid (timestamp, timestamp) cut".format(cut))
		try:
			b, e = cut
			if not b:
				b = 0
			if not e:
				e = get_duration(input_filename)
			d = e - b
			'''The order of ffmpeg -i command matters
			'''
			if fast:
				if b:
					command += [ '-ss', str(b), '-i', input_filename, '-t', str(d) ]
				else:
					command += [ '-i', input_filename, '-t', str(d) ]
			else:
				if b:
					command += [ '-i', input_filename, '-ss', str(b), '-t', str(d) ]
				else:
					command += [ '-i', input_filename, '-t', str(d) ]
		except Exception as e:
			raise FFmpegException("{} not a valid (timestamp, timestamp) cut: {}".format(cut, e))
	command += [ output_filename ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ffmpeg_executable]+command
def parse_output(out, err=b'', returncode=None):
	def _parse(b, prefix='STDOUT', encoding=stream_encoding):
		line = b.decode(encoding).rstrip()
		debug(prefix+' '+line)
	for b in err.splitlines():
		_parse(b, 'STDERR')
	for b in out.splitlines():
		_parse(b)
	return returncode or 0
def ffmpeg(input_filename, **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		error("Failed to open '{}'".format(input_filename))
		return -1
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
		returncodes = []
		a = returncodes.append
		for n, (b, e) in enumerate(splits, start=1):
			ofn = output_file_pattern.format(n)
			command = FFmpeg_command(input_filename, output_filename=ofn, cut=(b,e), **kwargs)
			debug("Running "+" ".join(command) )
			proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = proc.communicate()
			r = parse_output(out, err, proc.returncode)
			if not r:
				debug("part {} exited normally".format(n))
			else:
				error("part {} exited {}".format(n, r))
			a(r)
		return -1 if any((0 != r) for r in returncodes) else 0
	else:
		command = FFmpeg_command(input_filename, **kwargs)
		debug("Running "+" ".join(command))
		proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()
		return parse_output(out, err, proc.returncode)
