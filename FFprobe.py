#!/usr/bin/env python3
import datetime
import decimal
import fractions
import json
import subprocess
import sys

from . import *

import logging
logger = logging.getLogger('' if __name__ == '__main__' else __name__)
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical

class FFprobeException(Exception):
	pass

if sys.platform.startswith('win'):
	executable = 'FFPROBE.EXE'
else:
	executable = 'ffprobe'

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
def parse_output(stdout_contents):
	p = json.loads(stdout_contents)
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
	proc = subprocess.Popen([executable]+command+[input_arg],
		stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE) # stderr goes to console
	outs, _ = proc.communicate()
	debug( "FFprobe output {:,} B".format(len(outs)) )
	if proc.returncode == 0: # success
		return parse_output(outs.decode(encoding))


if '__main__' == __name__:
	import sys
	for arg in sys.argv[1:]:
		print(ffprobe(arg))
		print()


