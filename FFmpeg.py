#!/usr/bin/env python3
import fractions
import os.path
import string
import subprocess
import sys

from . import *

if sys.platform.startswith('win'):
	ffmpeg_executable = 'FFMPEG.EXE'
	ffprobe_executable = 'FFPROBE.EXE'
else:
	ffmpeg_executable = 'ffmpeg'
	ffprobe_executable = 'ffprobe'

class FFmpegException(SplitterException):
	pass

#def get_video_size(input_filename):
#def get_audio_sample_rate(input_filename):
def get_frame_rate(input_filename, encoding=stream_encoding):
	'''
	ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=noprint_wrappers=1:nokey=1
	'''
	command = [ 'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate', '-of', 'default=noprint_wrappers=1' ]
	proc = subprocess.Popen(command+[input_filename], stdout=subprocess.PIPE) # stderr goes to console
	outs, _ = proc.communicate()
	assert not proc.returncode
	for b in outs.splitlines():
		line = b.decode(encoding).rstrip()
		if 'avg_frame_rate' in line:
			return fractions.Fraction(line[len('avg_frame_rate')+1:])
	raise FFmpegException(outs)

def FFmpeg_command(input_filename, output_filename=None, **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not output_filename:
		output_filename = filepart+'_Cut'+ext
	commands = kwargs.pop('commands', [])
	if 'cut' in kwargs:
		cut = kwargs.pop('cut')
		if not isinstance(cut, (list, tuple)):
			raise FFmpegException("{} not valid splits".format(cut))
		try:
			commands += [ '-split-chunk', '{}:{}'.format(cut[0] or '', cut[1] or '') ]
		except:
			raise FFmpegException("{} not valid splits".format(cut))
	commands += [ output_filename ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ ffmpeg_executable, '-i', input_filename ]+commands
def FFmpeg_probe(filename):
	command = [ ffprobe_executable, filename ]
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate()
	return not parse_output(out, err, proc.returncode)
def parse_output(out, err='', returncode=None):
	def _parse(b, prefix='STDOUT', encoding='ASCII'):
		line = b.decode(encoding).rstrip()
		if 'Bad Parameter' in line:
			raise FFmpegException(line)
		elif line.upper().startswith('WARNING:'): # wrap warnings
			warning(line[9:])
		elif line.startswith('Appending:') and line.endswith('100)'): # progress
			return line
		else:
			debug(prefix+' '+line)
	for b in err.splitlines():
		_parse(b, 'STDERR')
	'''FFmpeg sends most output to stderr'''
	#for b in out.splitlines():
	#	_parse(b)
	return returncode or 0
def FFmpeg(input_filename, **kwargs):
	fps = 29.970
	debug('TODO: for the purposes of converting frame numbers, FPS is fixed at {}'.format(fps))
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		error("Failed to open '{}'".format(input_filename))
		return -1
	output_file_pattern = kwargs.pop('output_file_pattern', filepart+'-{:03d}'+'.MP4')
	debug("Running probe...")
	if not FFmpeg_probe(input_filename):
		raise FFmpegException("Failed to open '{}'".format(input_filename))
	if 'frames' in kwargs:
		debug("Converting frames")
		kwargs['cuts'] = [ (int(b)/fps if b else '', int(e)/fps if e else '') for (b, e) in kwargs.pop('frames') ]
	if 'splits' in kwargs:
		splits = kwargs.pop('splits')
		debug("Running {} commands".format(len(splits)) )
		returncodes = []
		a = returncodes.append
		for n, (b, e) in enumerate(splits, start=1):
			ofn = output_file_pattern.format(n)
			command = FFmpeg_command(input_filename, output_filename=ofn, cut=(b,e), **kwargs)
			debug("Running "+" ".join(command))
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
