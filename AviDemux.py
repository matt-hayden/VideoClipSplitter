#!/usr/bin/env python3
#from datetime import timedelta
import os.path
from pprint import pformat
import string
import subprocess
import sys

from . import *

if sys.platform.startswith('win'):
	avidemux_executable = 'AVIDEMUX.EXE'
else:
	avidemux_executable = 'avidemux3_cli'

# The first entry here becomes the default
containers = [
	('AVI',		'odmlType=1'),
	('MKV',		'forceDisplayWidth=False', 'displayWidth=1280'),
	('MP4V2',	'optimize=0', 'add_itunes_metadata=0'),
	('MP4',		'muxerType=0', 'useAlternateMp3Tag=True'),
	('OGM') ]

dirname, _ = os.path.split(__file__)
with open(os.path.join(dirname,'AviDemux.template')) as fi:
	avidemux_script_template = fi.read()

class AviDemuxException(SplitterException):
	pass
class TinyPyException(AviDemuxException):
	pass
#
def wrap(*args, **kwargs):
	'''return lines that form a repr() suitable for TinyPy'''
	lines = pformat(*args, **kwargs).splitlines()
	if any(255 < len(_) for _ in lines):
		raise TinyPyException("Line limit 255 reached")
	for n, line in enumerate(lines, start=1-len(lines)):
		yield line+'\\' if n else line

def AviDemux_command(input_filename, output_file_pattern='', script_filename='', container=containers[0], **kwargs):
	if 255 < len(os.path.abspath(input_filename)):
		raise TinyPyException("Filename {} too long".format(input_filename))
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not script_filename:
		script_filename = basename+'.AviDemux.py'
	if output_file_pattern:
		output_filepart, output_ext = os.path.splitext(output_file_pattern) # inelegant
	else:
		output_filepart, output_ext = filepart, ext
	video_filters = kwargs.pop('video_filters', [])
	parts, frames = [], []
	if 'splits' in kwargs:
		# expects decimal seconds
		parts = kwargs.pop('splits')
	if 'frames' in kwargs:
		frames = [ (b or None, e or None) for (b, e) in kwargs.pop('frames') ]
	if parts and frames:
		warning("Refusing to split on both second and frame number, using {}".format(parts))
	t = string.Template(kwargs.pop('template', None) or avidemux_script_template)
	# prepare local variables for TinyPy:
	if parts:
		parts = '\n'.join(wrap(parts))
	if frames:
		frames = '\n'.join(wrap(frames))
	loc = locals()
	#
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	for k, v in loc.items():
		if not k.startswith('_'):
			debug("AviDemux variable: {}={}".format(k, v))
	with open(script_filename, 'w') as ofo:
		ofo.write(t.substitute(loc))
	return [ avidemux_executable, '--run', script_filename ]
def AviDemux_probe(filename, encoding='ASCII'):
	'''TODO: AviDemux doesn't have an info command (right?)
	'''
	proc = subprocess.Popen([ 'file', filename ], stdout=subprocess.PIPE)
	out, _ = proc.communicate()
	if out:
		line = [b.decode(encoding) for b in out]
		debug("file: "+line[0])
		if any(w in line[0] for w in [ 'AVI', 'MPEG' ]):
			return True
	return False
def parse_output(out, err='', returncode=None):
	#TODO: incomplete
	def _parse(b, prefix='STDOUT', encoding='ASCII'):
		line = b.decode(encoding).rstrip()
		if 'PerfectAudio' not in line: # silently drop TONS of output
			debug(prefix+' '+line)
	for b in err.splitlines():
		_parse(b, prefix='STDERR')
	for b in out.splitlines():
		_parse(b)
	return returncode
def avidemux(input_filename, output_file_pattern='', **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		error("Failed to open '{}'".format(input_filename))
		return -1
	debug("Running probe...")
	'''
	This is different than the other wrappers: exception is not raised when probe fails, rather silently returns error code
	'''
	if not AviDemux_probe(input_filename):
		error("Failed to open '{}'".format(input_filename))
		return -1
	command = AviDemux_command(input_filename, **kwargs)
	debug("Running "+" ".join(command))
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate()
	return parse_output(out, err, proc.returncode)
