
import os.path
import string
import subprocess
import sys


try:
	"""
	If used in a package, package logging functions are used instead of stderr.
	"""
	from . import debug, info, warning, error, fatal
except:
	def error(*args, **kwargs):
		print(*args, file=sys.stderr, **kwargs)
	debug = info = warning = fatal = error

from . import ConverterBase, SplitterException


class AviDemuxException(SplitterException):
	pass

# The first entry here becomes the default
containers = [
	('AVI',		'odmlType=1'),
	('MKV',		'forceDisplayWidth=False', 'displayWidth=1280'),
	('MP4V2',	'optimize=0', 'add_itunes_metadata=0'),
	('MP4',		'muxerType=0', 'useAlternateMp3Tag=True'),
	('OGM') ]
debug( "Default container is {}".format(containers[0]) )

dirname, _ = os.path.split(__file__)
with open(os.path.join(dirname,'AviDemux.template')) as fi:
	script_template = fi.read()


def probe(*args):
	'''
	AviDemux doesn't have an info command (right?), so this is a wrapper for the 'file' utility
	'''
	def parse_line(b, prefix='', encoding=stream_encoding):
		line = b.decode(encoding).rstrip()
		return any(w in line for w in [ 'AVI', 'MPEG' ])
	for filename in args:
		proc = subprocess.Popen([ 'file', filename ],
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE)
		assert not proc.returncode
		stdout_contents, _ = proc.communicate()
		if not stdout_contents:
			return False
		lines = stdout_contents.split(b'\n')
		if not parse_line(lines[0]):
			return False
	return True
class AviDemuxConverter(ConverterBase):
	@staticmethod
	def check_filenames(*args):
		for filename in args:
			if 255 < len(os.path.abspath(filename)):
				raise TinyPyException("Filename too long")
	@staticmethod
	def match_filenames(*args):
		r = []
		y = r.append
		for arg in args:
			_, ext = os.path.splitext(arg)
			if ext.upper() in ( '.AVI', '.DIVX', '.FLV', '.MKV', '.OGM', '.WEBM', '.XVID' ):
				y(arg)
		return r
	def __init__(self, **kwargs):
		self.dry_run = kwargs.pop('dry_run', None)
		if sys.platform.startswith('win'):
			self.executable = 'AVIDEMUX.EXE'
		else:
			self.executable = 'avidemux3_cli'
		self.extra_options = kwargs
	def get_commands(self, input_filename,
			output_filename='',
			script_filename='',
			container=containers[0],
			video_filters=[],
			**kwargs):
		options = kwargs
		self.check_filenames(input_filename)
		dirname, basename = os.path.split(input_filename)
		filepart, ext = os.path.splitext(basename)
		if not script_filename:
			script_filename = basename+'.AviDemux.py'
		if output_filename:
			output_filepart, output_ext = os.path.splitext(output_filename) # inelegant
		else:
			output_filepart, output_ext = filepart, ext
		output_ext = options.pop('output_ext', output_ext.upper())
		if video_filters:
			container = containers[1]
		parts, frames = [], []
		if 'splits' in options:
			# expects decimal seconds
			parts = options.pop('splits')
		if 'frames' in options:
			frames = [ (b or None, e or None) for (b, e) in options.pop('frames') ]
		if parts and frames:
			warning("Refusing to split on both second and frame number, using {}".format(parts))
		t = string.Template(options.pop('template', script_template))
		# prepare local variables for TinyPy:
		if parts:
			parts = '\n'.join(wrap(parts))
		if frames:
			frames = '\n'.join(wrap(frames))
		loc = locals()
		#
		for k, v in options.items():
			debug("Extra parameter unused: {}={}".format(k, v))
		for k, v in loc.items():
			if not k.startswith('_'):
				debug("AviDemux variable: {}={}".format(k, v))
		with open(script_filename, 'w') as ofo:
			ofo.write(t.substitute(loc))
		return [ [ self.executable, '--run', script_filename ] ]
	def parse_output(self, streams, **kwargs):
		'''
		Encoding is Latin-1 because AviDemux emits control characters
		'''
		stdout_contents, stderr_contents = streams
		debug( "{:,}B of stdout".format(len(stdout_contents)) )
		debug( "{:,}B of stderr".format(len(stderr_contents)) )
		for b in avoid_duplicates(stderr_contents.split(b'\n'), encoding='latin-1'):
			parse_line(b, prefix='STDERR')
		for b in avoid_duplicates(stdout_contents.split(b'\n'), encoding='latin-1'):
			parse_line(b)
		return kwargs.pop('returncode')==0, []
def parse_line(b, prefix='STDOUT', encoding='latin-1'):
	line = b.decode(encoding).rstrip()
	if not line or 'PerfectAudio' in line: # TONS of output
		return
	if line.startswith('[Script]'):
		line = line[len('[Script]')+1:]
		engine, line = line.split(' ', 1)
		if engine=='Tinypy' and line.startswith('INFO'): # INFO - 
			info(line[len('INFO - '):])
		else:
			debug(engine+' '+line)
	else:
		debug(prefix+' '+line)
###
if sys.platform.startswith('win'):
	executable = 'AVIDEMUX.EXE'
else:
	executable = 'avidemux3_cli'
debug("AviDemux is "+executable)
def AviDemux_command(input_filename, output_filename='', script_filename='', container=containers[0], **kwargs):
	if 255 < len(os.path.abspath(input_filename)):
		raise TinyPyException("Filename {} too long".format(input_filename))
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not script_filename:
		script_filename = basename+'.AviDemux.py'
	if output_filename:
		output_filepart, output_ext = os.path.splitext(output_filename) # inelegant
	else:
		output_filepart, output_ext = filepart, ext
	output_ext = kwargs.pop('output_ext', output_ext.upper())
	video_filters = kwargs.pop('video_filters', [])
	if video_filters:
		container = containers[1]
	parts, frames = [], []
	if 'splits' in kwargs:
		# expects decimal seconds
		parts = kwargs.pop('splits')
	if 'frames' in kwargs:
		frames = [ (b or None, e or None) for (b, e) in kwargs.pop('frames') ]
	if parts and frames:
		warning("Refusing to split on both second and frame number, using {}".format(parts))
	t = string.Template(kwargs.pop('template', None) or script_template)
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
	return [ executable, '--run', script_filename ]
def parse_output(outs, errs='', returncode=None, stream_encoding='latin-1'):
	'''
	Encoding is Latin-1 because AviDemux emits control characters
	'''
	def parse_line(b, prefix='STDOUT', encoding=stream_encoding):
		line = b.decode(encoding).rstrip()
		if not line:
			pass
		elif line.startswith('[Script]'):
			line = line[9:]
			engine, line = line.split(' ', 1)
			if engine=='Tinypy' and line.startswith('INFO'): # INFO - 
				info(line[7:])
			else:
				debug(engine+' '+line)
		elif 'PerfectAudio' in line: # silently drop TONS of output
			pass
		else:
			debug(prefix+' '+line)
	for b in avoid_duplicates(errs.splitlines(), encoding=stream_encoding):
		parse_line(b, prefix='STDERR')
	for b in avoid_duplicates(outs.splitlines(), encoding=stream_encoding):
		parse_line(b)
	return returncode
### EOF
