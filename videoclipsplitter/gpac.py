
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

from . import ConverterBase, SplitterException, progress_bar, stream_encoding
from .chapters import make_chapters_file
from .FFprobe import get_frame_rate


class GpacException(SplitterException):
	pass


common_chapter_spec_element = '''CHAPTER${n}=$timestamp
CHAPTER${n}NAME=$name
'''


def probe(*args):
	GpacConverter.check_filenames(*args)
	m = GpacConverter()
	for filename in args:
		command = [ m.executable, '-info', filename, '-std' ]
		proc = subprocess.Popen(command,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
		r, _ = m.parse_output(proc.communicate(), returncode=proc.returncode)
		if not r:
			return False
	return True
class GpacConverter(ConverterBase):
	can_chapter = True
	can_split = True
	@staticmethod
	def match_filenames(*args):
		r = []
		y = r.append
		for arg in args:
			_, ext = os.path.splitext(arg)
			if ext.upper() in ( '.3GP', '.3G2', '.F4V', '.M4V', '.MJ2', '.MOV', '.MP4', '.MPG' ):
				y(arg)
		return r
	@staticmethod
	def check_filenames(*args):
		for filename in args:
			if '+' in filename:
				raise GpacException("MP4Box is intolerant of filenames with special characters: '{}'".format(filename))
		return True
	def __init__(self, **kwargs):
		self.dry_run = kwargs.pop('dry_run', None)
		if sys.platform.startswith('win'):
			self.executable = 'MP4BOX.EXE'
		else:
			self.executable = 'MP4Box'
		self.extra_options = kwargs
	def get_commands(self, input_filename,
					 output_filename='',
					 **kwargs):
		options = kwargs
		self.check_filenames(input_filename)
		dirname, basename = os.path.split(input_filename)
		filepart, ext = os.path.splitext(basename)
		splits, syntax = [], []
		if 'splits' in options:
			splits = options.pop('splits')
		elif 'frames' in options:
			fps = get_frame_rate(input_filename)
			debug( "Converting frame cuts to decimal second cuts at {:.2f} fps".format(fps) )
			splits = [ (int(b)/fps if b else '', int(e)/fps if e else '') for (b, e) in options.pop('frames') ]
		elif 'chapters' in options: # these are pairs
			output_filename = output_filename or '{filepart}_Chapters.MP4'
			chapters_filename = options.pop('chapters_filename', '{basename}.chapters')
			try:
				chapters_filename = chapters_filename.format(**locals())
			except:
				warning("chapters_filename={}, which is probably not what you intended".format(chapters_filename))
			if make_chapters_file(options.pop('chapters'), chapters_filename):
				syntax += [ '-chap', chapters_filename ]
				syntax += [ '-add-item', chapters_filename ]
		else:
			output_filename = output_filename or '{filepart}_Cut.MP4'
		for k, v in options.items():
			debug("Extra parameter unused: {}={}".format(k, v))
		if splits:
			output_filename = output_filename or '{filepart}-{n:03d}.MP4'
			for n, (b, e) in enumerate(splits, start=1):
				try:
					my_filename = output_filename.format(**locals())
				except:
					warning("output_filename={}, which is probably not what you intended".format(my_filename))
				syntax_part = syntax+[ '-split-chunk', '{}:{}'.format(b or '', e or '') ]
				yield [ self.executable, '-cat', input_filename ]+syntax_part+[ '-new', my_filename ]
		else:
			yield [ self.executable, '-cat', input_filename ]+syntax+[ '-new', output_filename ]
	def parse_output(self, streams, **kwargs):
		_, stderr_contents = streams
		for b in stderr_contents.split(b'\n'):
			parse_line(b, prefix='STDERR')
		return kwargs.pop('returncode', 0) == 0, []
def parse_line(b,
			   prefix='STDOUT',
			   progress=print if sys.stdout.isatty() else (lambda x: None),
			   encoding=stream_encoding):
	line = b.decode(encoding).rstrip()
	if not line:
		return
	#if line.endswith('100)'):
	if  '\r' in line:
		_, lline = line.rsplit('\r', 1)
		for p in [ 'Appending:', 'ISO File Writing:', 'Splitting:' ]:
			if lline.startswith(p):
				progress(lline)
				break
		else:
			debug(prefix+' '+lline)
	return
	for s in ['Bad Parameter', 'No suitable media tracks to cat']:
		if s in line:
			raise GpacException(line)
	if line.upper().startswith('WARNING:'): # wrap warnings
		warning(line[len('WARNING:'):])
	else:
		debug(prefix+' '+line)
###
if sys.platform.startswith('win'):
	mp4box_executable = 'MP4BOX.EXE'
else:
	mp4box_executable = 'MP4Box'
debug("MP4Box is {}".format(mp4box_executable))
def MP4Box_command(input_filename,
				   output_filename='{filepart}_Cut.MP4',
				   chapters_filename='{basename}.chapters',
				   **kwargs):
	if '+' in input_filename: raise GpacException("MP4Box is intolerant of filenames with special characters: '{}'".format(input_filename))
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	commands = kwargs.pop('commands', [])
	if 'cut' in kwargs:
		cut = kwargs.pop('cut')
		if not isinstance(cut, (list, tuple)):
			raise GpacException("{} not valid splits".format(cut))
		try:
			b, e = cut
			if not b:
				b = ''
			if not e:
				e = ''
			commands += [ '-split-chunk', '{}:{}'.format(b, e) ]
		except Exception as e:
			raise GpacException("{} not valid splits: {}".format(cut, e))
	if 'chapters' in kwargs: # these are pairs
		try:
			chapters_filename = chapters_filename.format(**locals())
		except:
			warning("chapters_filename={}, which is probably not what you intended".format(chapters_filename))
		if make_chapters_file(kwargs.pop('chapters'), chapters_filename):
			commands += [ '-chap', chapters_filename ]
			commands += [ '-add-item', chapters_filename ]
	try:
		output_filename = output_filename.format(**locals())
	except:
		warning("output_filename={}, which is probably not what you intended".format(output_filename))
	commands += [ '-new', output_filename ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ mp4box_executable, '-cat', input_filename ]+commands
def parse_output(out, err='', returncode=None):
	def parse_line(b, prefix='STDOUT', encoding=stream_encoding):
		line = b.decode(encoding).rstrip()
		if any(s in line for s in ['Bad Parameter', 'No suitable media tracks to cat']):
			raise GpacException(line)
		elif line.upper().startswith('WARNING:'): # wrap warnings
			warning(line[9:])
		elif any(line.startswith(p) for p in [ 'Appending:', 'ISO File Writing:', 'Splitting:' ]) and line.endswith('100)'): # progress
			return line
		else:
			debug(prefix+' '+line)
	for b in err.splitlines():
		parse_line(b, 'STDERR')
	'''MP4Box sends most output to stderr'''
	#for b in out.splitlines():
	#	parse_line(b)
	return returncode or 0
### EOF
