
from datetime import timedelta
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

from . import ConverterBase, SplitterException, progress_bar
from .chapters import make_chapters_file


class MkvMergeException(SplitterException):
	pass

dirname, _ = os.path.split(__file__)
with open(os.path.join(dirname,'MkvMerge.template')) as fi:
	options_file_template = fi.read()


def probe(*args):
	m = MkvMergeConverter()
	for filename in args:
		proc = subprocess.Popen([ m.executable, '-i', filename ],
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
		r, _ = m.parse_output(proc.communicate(), returncode=proc.returncode)
		if not r:
			return False
	return True
class MkvMergeConverter(ConverterBase):
	@staticmethod
	def match_filenames(*args, modest=True):
		r = []
		y = r.append
		for arg in args:
			_, ext = os.path.splitext(arg)
			ext = ext.upper()
			if ext not in ( '.ASF', '.WMV' ):
				if modest and ext in ( '.MOV', '.MPG', '.MP4', '.M4V' ):
					break
				y(arg)
		return r
	def __init__(self, **kwargs):
		self.dry_run = kwargs.pop('dry_run', None)
		if sys.platform.startswith('win'):
			self.executable = 'MKVMERGE.EXE'
		else:
			self.executable = 'mkvmerge'
		self.extra_options = kwargs
	def get_commands(self, input_filename,
					 output_filename='{filepart}.MKV',
					 options_filename='{basename}.MkvMerge.options',
					 chapters_filename='{basename}.chapters',
					 split_style='',
					 **kwargs):
		warning("MkvMerge currently operates AFTER keyframes. Your output may not exactly match your cuts.")
		options = kwargs
		dirname, basename = os.path.split(input_filename)
		filepart, ext = os.path.splitext(basename)
		try:
			options_filename = options_filename.format(**locals())
		except:
			warning( "options_filename={}, which is probably not what you intended".format(options_filename) )
		# output_filename needs to be formed to be used for template
		# substitution below
		try:
			output_filename = output_filename.format(**locals())
		except:
			warning( "output_filename={}, which is probably not what you intended".format(output_filename) )
		commands = []
		if 'title' in options:
			commands += [ '--title', options.pop('title') ]
		if 'splits' in options:
			split_style = 'parts'
			my_pairs = [ (timedelta(seconds=float(b)) if b else '', timedelta(seconds=float(e)) if e else '') for (b, e) in options.pop('splits') ]
		if 'frames' in options:
			split_style = 'parts-frames'
			my_pairs = [ (b or '', e or '') for (b, e) in options.pop('frames') ]
		if 'only_chapters' in options:
			split_style = 'chapters'
			my_pairs = [ (b or '', e or '') for (b, e) in options.pop('only_chapters') ]
		if split_style:
			commands += [ '--link', '--split' ]
			commands += [ split_style+':'+','.join(( '{}-{}'.format(*p) for p in my_pairs )) ]
		if 'chapters' in options: # these are pairs
			try:
				chapters_filename = chapters_filename.format(**locals())
			except:
				warning("chapters_filename={}, which is probably not what you intended".format(chapters_filename))
			if make_chapters_file(options.pop('chapters'), chapters_filename):
				commands += [ '--chapters', chapters_filename ]
				commands += [ '--attach-file', chapters_filename ]
		command_lines = '\n'.join(commands)
		t = string.Template(options.pop('template', None) or options_file_template)
		with open(options_filename, 'w') as ofo:
			ofo.write(t.substitute(locals()))
		for k, v in options.items():
			debug("Extra parameter unused: {}={}".format(k, v))
		return [ [ self.executable, '@'+options_filename ] ]
	def parse_output(self, streams, **kwargs):
		stdout_contents, stderr_contents = streams
		debug( "{}B of stdout".format(len(stdout_contents)) )
		debug( "{}B of stderr".format(len(stderr_contents)) )
		for b in stderr_contents.split(b'\n'):
			parse_line(b, prefix='STDERR')
		for b in stdout_contents.split(b'\n'):
			parse_line(b)
		return kwargs.pop('returncode')==0, []
def parse_line(b,
			   prefix='STDOUT',
			   progress=print if sys.stdout.isatty() else (lambda x: None),
			   encoding='UTF-8'):
	line = b.decode(encoding).rstrip()
	if not line:
		return
	#if line.startswith('Progress:') and line.endswith('%'):
	if '\r' in line:
		progress(line.rsplit('\r', 1)[-1])
		return
	if line.startswith('Error:'):
		raise MkvMergeException(line[len('Error:')+1:])
	elif 'unsupported container:' in line:
		raise MkvMergeException(line)
	elif 'This corresponds to a delay' in line:
		warning(line)
	elif 'audio/video synchronization may have been lost' in line:
		warning(line)
	else:
		debug(prefix+' '+line)


if sys.platform.startswith('win'):
	mkvmerge_executable = 'MKVMERGE.EXE'
else:
	mkvmerge_executable = 'mkvmerge'
debug("MkvMerge is {}".format(mkvmerge_executable))
def MkvMerge_command(input_filename,
					 output_filename='{filepart}.MKV',
					 options_filename='{basename}.MkvMerge.options',
					 chapters_filename='{basename}.chapters',
					 split_style='',
					 **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	try:
		options_filename = options_filename.format(**locals())
	except:
		warning( "options_filename={}, which is probably not what you intended".format(options_filename) )
	# output_filename needs to be formed to be used for template
	# substitution below
	try:
		output_filename = output_filename.format(**locals())
	except:
		warning( "output_filename={}, which is probably not what you intended".format(output_filename) )
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
	t = string.Template(kwargs.pop('template', None) or options_file_template)
	with open(options_filename, 'w') as ofo:
		ofo.write(t.substitute(locals()))
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ mkvmerge_executable, '@'+options_filename ]
def parse_output(out, err='', returncode=None):
	def parse_line(b, prefix='STDOUT', encoding='ASCII'):
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
		parse_line(b, prefix='STDERR')
	for b in out.splitlines():
		parse_line(b)
	return returncode or 0
### EOF
