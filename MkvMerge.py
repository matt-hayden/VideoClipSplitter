#!/usr/bin/env python3
from datetime import timedelta
import os.path
import shlex
import string
import subprocess
import sys

from . import *
from .chapters import make_chapters_file

if sys.platform.startswith('win'):
	mkvmerge_executable = 'MKVMERGE.EXE'
else:
	mkvmerge_executable = 'mkvmerge'
debug("MkvMerge is {}".format(mkvmerge_executable))

dirname, _ = os.path.split(__file__)
with open(os.path.join(dirname,'MkvMerge.template')) as fi:
	mkvmerge_options_file_template = fi.read()

class MkvMergeException(SplitterException):
	pass

def MkvMerge_command(input_filename,
					 output_file_pattern='{filepart}.MKV',
					 options_filename='{basename}.MkvMerge.options',
					 chapters_filename='{basename}.chapters',
					 split_style='',
					 **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	try:
		options_filename = options_filename.format(**locals())
	except:
		warning("options_filename={}, which is probably not what you intended".format(options_filename))
	# output_file_pattern needs to be formed to be used for template
	# substitution below
	try:
		output_file_pattern = output_file_pattern.format(**locals())
	except:
		warning("output_file_pattern={}, which is probably not what you intended".format(output_file_pattern))
	commands = kwargs.pop('commands', [])
	if 'title' in kwargs:
		commands += [ '--title', kwargs.pop('title') ]
	if 'splits' in kwargs:
		split_style = 'parts'
		my_pairs = [ (timedelta(seconds=float(b)) if b else '', timedelta(seconds=float(e)) if e else '') for (b, e) in kwargs.pop('splits') ]
	if 'frames' in kwargs:
		split_style = 'parts-frames'
		my_pairs = [ (b or '', e or '') for (b, e) in kwargs.pop('frames') ]
	if 'only_chapters' in kwargs:
		split_style = 'chapters'
		my_pairs = [ (b or '', e or '') for (b, e) in kwargs.pop('only_chapters') ]
	if split_style:
		commands += [ '--link', '--split' ]
		commands += [ split_style+':'+','.join(( '{}-{}'.format(*p) for p in my_pairs )) ]
	if 'chapters' in kwargs: # these are pairs
		try:
			chapters_filename = chapters_filename.format(**locals())
		except:
			warning("chapters_filename={}, which is probably not what you intended".format(chapters_filename))
		if make_chapters_file(kwargs.pop('chapters'), chapters_filename):
			commands += [ '--chapters', chapters_filename ]
			commands += [ '--attach-file', chapters_filename ]
	command_lines = '\n'.join(commands)
	t = string.Template(kwargs.pop('template', None) or mkvmerge_options_file_template)
	with open(options_filename, 'w') as ofo:
		ofo.write(t.substitute(locals()))
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ mkvmerge_executable, '@'+options_filename ]
def MkvMerge_probe(filename):
	proc = subprocess.Popen([ mkvmerge_executable, '-i', filename ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate()
	return not parse_output(out, err, proc.returncode)
def parse_output(out, err='', returncode=None):
	def _parse(b, prefix='STDOUT', encoding='ASCII'):
		line = b.decode(encoding).rstrip()
		if line.startswith('Error:'):
			raise MkvMergeException(line[7:])
		elif 'unsupported container:' in line:
			raise MkvMergeException(line)
		elif 'This corresponds to a delay' in line:
			warning(line)
		elif 'audio/video synchronization may have been lost' in line:
			warning(line)
		elif line.startswith('Progress:') and line.endswith('%'): # progress
			return line
		else:
			debug(prefix+' '+line)
	for b in err.splitlines():
		_parse(b, prefix='STDERR')
	for b in out.splitlines():
		_parse(b)
	return returncode or 0
def mkvmerge(input_filename, dry_run=False, **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		raise SplitterException("'{}' not found".format(input_filename))
	debug("Running probe...")
	if not MkvMerge_probe(input_filename):
		raise MkvMergeException("Failed to open '{}'".format(input_filename))
	command = MkvMerge_command(input_filename, **kwargs)
	if not dry_run:
		debug("Running "+' '.join(command))
		warning("TODO: MkvMerge currently operates AFTER keyframes. Your output may not exactly match your cuts.")
		proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()
		return not parse_output(out, err, proc.returncode)
	else:
		print(' '.join(shlex.quote(s) for s in command))
