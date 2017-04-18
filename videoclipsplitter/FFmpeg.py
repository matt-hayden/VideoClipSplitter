
import os, os.path
import subprocess
import sys


try:
	from . import debug, info, warning, error, fatal
except ImportError:
	debug = info = warning = error = fatal = print


from .util import *
from .FFprobe import ffprobe as probe


warnings = [ 'deprecated pixel format used, make sure you did set range correctly',
			 'DTS discontinuity',
			 'Invalid timestamp',
			 'Non-increasing DTS',
			 'VBV buffer size not set, muxing may fail' ]


class FFmpegException(SplitterException):
	pass


class FFmpegConverter(ConverterBase):
	can_split = True
	@staticmethod
	def match_filenames(*args):
		r = []
		y = r.append
		for arg in args:
			_, ext = os.path.splitext(arg)
			if ext not in ( '.ASF', '.WMV' ):
				y(arg)
		return r
	def __init__(self, **kwargs):
		self.dry_run = kwargs.pop('dry_run', None)
		if sys.platform.startswith('win'):
			self.executable = 'FFMPEG.EXE'
		else:
			self.executable = 'ffmpeg'
		self.extra_options = kwargs
	def get_commands(self, input_source,
			output_filename='{filepart}-%03d{output_ext}',
			**kwargs):
		options = kwargs
		dirname, basename = os.path.split(input_source)
		filepart, ext = os.path.splitext(basename)
		ext = ext.upper()
		output_ext = options.pop('output_ext', ext)
		if output_ext in ['.ASF', '.WMV']:
			warning("Direct stream copy disabled")
			output_ext = '.NUT'
		filters = options.pop('filters', [])
		### some arguments have to go here (before input source)
		command = [ '-i', input_source ]
		if 'title' in options:
			command += [ '-metadata', 'title='+options.pop('title') ]
		if 'frames' in options:
			command += '-f segment -map 0 -flags +global_header'.split()
			frame_splits = sorted(set(f for f in flatten(options.pop('frames')) if f)-set([0, '0']), key=float)
			command += [ '-segment_frames', ','.join(frame_splits) ]
		elif 'splits' in options: # these are decimal times
			command += '-f segment -map 0 -flags +global_header'.split()
			time_splits = sorted(set(t for t in flatten(options.pop('splits')) if t)-set([0, '0']), key=float)
			command += [ '-segment_times', ','.join(time_splits) ]
		command += filters or [ '-c:v', 'copy', '-c:a', 'copy' ]
		try:
			output_filename = output_filename.format(**locals())
		except:
			warning("Output filename is {}, which is probably not what you want".format(output_filename))
		command += [ output_filename ]
		for k, v in options.items():
			debug("Extra parameter unused: {}={}".format(k, v))
		return [ [self.executable, '-nostdin']+command ]
	def parse_output(self, streams, **kwargs):
		_, stderr_contents = streams
		debug( "{}B of stderr".format(len(stderr_contents)) )
		if stderr_contents:
			for b in avoid_duplicates(stderr_contents.split(b'\n')):
				parse_line(b)
		return kwargs.pop('returncode', 0) == 0, []
###
def parse_line(b,
			   prefix='STDERR',
			   progress=print if sys.stdout.isatty() else (lambda x: None),
			   warnings=warnings,
			   encoding=stream_encoding):
	#lastframeline = ''
	line = b.decode(encoding).rstrip()
	if not line:
		return
	if line.startswith('frame='): # progress indicator
		#lastframeline = line
		#return line
		progress(line)
		return
	if 'Unrecognized option' in line:
		raise FFmpegException(line)
	elif 'At least one output file must be specified' in line:
		raise FFmpegException(line)
	elif 'Error opening filters!' in line:
		raise FFmpegException(line)
	elif 'Output file is empty, nothing was encoded' in line:
		#if lastframeline: error(lastframeline) #
		raise FFmpegException(line)
	elif 'Press [q] to stop, [?] for help' in line:
		warning('Running interactive (maybe try -nostdin if using ffmpeg later than the avconv fork)')
	else:
		for w in warnings:
			if w in line:
				warning(line)
				break
		else:
			debug(prefix+' '+line)
	#return(lastframeline) # progress bar
###
if sys.platform.startswith('win'):
	ffmpeg_executable = 'FFMPEG.EXE'
else:
	ffmpeg_executable = 'ffmpeg'
debug("FFmpeg is {}".format(ffmpeg_executable))

def FFmpeg_command(input_source, output_filename='{filepart}-%03d{output_ext}', **kwargs):
	dirname, basename = os.path.split(input_source)
	filepart, ext = os.path.splitext(basename)
	output_ext = kwargs.pop('output_ext', ext.upper())
	filters = kwargs.pop('filters', [])
	### arguments could go here before input source
	command = [ '-i', input_source ]
	if 'title' in kwargs:
		command += [ '-metadata', 'title='+kwargs.pop('title') ]
	if 'frames' in kwargs:
		command += '-f segment -map 0 -flags +global_header'.split()
		frame_splits = sorted(set(f for f in flatten(kwargs.pop('frames')) if f)-set([0, '0']), key=float)
		command += [ '-segment_frames', ','.join(frame_splits) ]
	elif 'splits' in kwargs: # these are decimal times
		command += '-f segment -map 0 -flags +global_header'.split()
		time_splits = sorted(set(t for t in flatten(kwargs.pop('splits')) if t)-set([0, '0']), key=float)
		command += [ '-segment_times', ','.join(time_splits) ]
	if ext.upper() in ['.ASF', '.WMV']:
		info("Direct stream copy disabled")
		output_ext = '.NUT'
	elif not filters:
		command += [ '-c:v', 'copy', '-c:a', 'copy' ]
	command.extend(filters)
	try:
		output_filename = output_filename.format(**locals())
	except:
		warning("Output filename is {}, which is probably not what you want".format(output_filename))
	command += [ output_filename ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	return [ffmpeg_executable, '-nostdin']+command
def parse_output(outs, errs='', returncode=None):
	warnings = [ 'deprecated pixel format used, make sure you did set range correctly',
				 'DTS discontinuity',
				 'Invalid timestamp',
				 'Non-increasing DTS',
				 'VBV buffer size not set, muxing may fail' ]
	def parse_line(b, prefix='STDOUT', warnings=warnings, encoding=stream_encoding):
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
		for b in avoid_duplicates(errs.splitlines()):
			parse_line(b, prefix='STDERR')
	#for b in outs.splitlines(): # FFmpeg doesn't believe in stdout
	#	parse_line(b)
	return returncode or 0
### EOF
