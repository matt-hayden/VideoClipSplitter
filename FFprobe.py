#!/usr/bin/env python3
import datetime
import decimal
import fractions
import json
import subprocess
import sys

from . import *
from .FFmpeg import FFmpegException
class FFprobeException(FFmpegException):
	pass

if sys.platform.startswith('win'):
	ffprobe_executable = 'FFPROBE.EXE'
else:
	ffprobe_executable = 'ffprobe'

def get_duration(input_arg, encoding=stream_encoding):
	if isinstance(input_arg, str): # is a filename
		p = ffprobe(input_arg)
	else:
		p = input_arg
	return datetime.timedelta(seconds=float(p['format']['duration']))
def get_frame_rate(input_arg, encoding=stream_encoding):
	if isinstance(input_arg, str): # is a filename
		p = ffprobe(input_arg)
	else:
		p = input_arg
	for s in p['streams']:
		if 'video' == s['codec_type']:
			return s['avg_frame_rate']
	return None
def get_video_size(input_arg, encoding=stream_encoding):
	if isinstance(input_arg, str): # is a filename
		p = ffprobe(input_arg)
	else:
		p = input_arg
	assert p
	for s in p['streams']:
		if 'video' == s['codec_type']:
			return s['width'], s['height']
	return None
def parse_output(outs):
	p = json.loads(outs)
	if not p:
		raise FFprobeException("FFprobe output parsed to: {}".format(p))
	debug("FFprobe JSON output has keys {}".format(', '.join(p.keys()) ) )
	for k, c in (('bit_rate', int), ('duration', decimal.Decimal), ('size', int)):
		if k in p['format']:
			p['format'][k] = c(p['format'][k])
	for s in p['streams']:
		if s['codec_type'] == 'audio':
			for k, c in (('bitrate', int), ('duration', decimal.Decimal)):
				if k in s:
					s[k] = c(s[k])
		if s['codec_type'] == 'video':
			for k, c in (('avg_frame_rate', fractions.Fraction), ('r_frame_rate', fractions.Fraction), ('duration', decimal.Decimal)):
				if k in s:
					s[k] = c(s[k])
	return p
def ffprobe(input_arg, command=['-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams'], encoding=stream_encoding):
	proc = subprocess.Popen([ffprobe_executable]+command+[input_arg], stdout=subprocess.PIPE) # stderr goes to console
	outs, _ = proc.communicate()
	debug("FFprobe output {:,} B".format(len(outs)) )
	if not proc.returncode:
		return parse_output(outs.decode(encoding))
	else:
		return False
