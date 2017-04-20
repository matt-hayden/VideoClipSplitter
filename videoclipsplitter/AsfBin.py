
from decimal import Decimal
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


errors = [ 'PROCESSING FAILED',
		   'At least one file cannot be processed',
		   'exists but it is too short' ]

class AsfBinException(SplitterException):
	pass


''' 
Application name is asfbin
ASFBIN - version asfbin 1.8.1.892. Copyright 2001-2010 by RadioActive.
Non-commercial version.
Visit www.radioactivepages.com for latest updates.
-
This tool cuts one or more fragments from ASF file(s) (*.WVM also) and writes it to a specified output file. It treats a list of input files as a one continuous WM file, thus it can be also used for joining ASF files together.
Because AsfBin doesn't need to index input file(s), it can skip damaged part of the file. In the other words it can repair damaged ASF files.
Use this tool only for evaluation purposes.

USAGE:
	asfbin [INPUT MEDIA FILES] -o <out_file> [SWITCHES]
	[INPUT MEDIA FILES] can be specified by:
	-i <in_file>       - input windows media file, can be repeated many times,
	-l <in_file_list>  - file containing list of files to join.
	[SWITCHES] are as follow:
	-sep               - write each segment to a separate file. Output file name will be treated like a name template where all occurences of {000} or {  } are replaced by the segment number. If {0} is not present, a number will be inserted right before the file name extension.
	-s <segments_list> - file containing list of segments to extract,
	-a <attrib_list>   - file containing list of attributes to set.
	-m <marker_list>   - file containing list of markers to set.
	-k <script_list>   - file containing list of scripts to set.

	-start <time>      - start copying from specified time,
	-dur <time>        - copy segment of specified time, these two switches can be repeated many times, each pair defining a new segment to extract
	-stop <time>       - stop copying at specified time,
	-invert            - invert selection. Specified segments will be removed,
	-repeat <n>        - repeat the entire resulting file <n> times.
	-istart            - don't wait for key frame. Files are joined without any advanced fitting. Can be used for files previously cut. By default copying starts after finding a key frame.
	-cvb               - always copy very beginning of input file discarding even finding key frame when joining too or more files,
	-brkaud            - Audio streams junctions will be marked as gap.
	-brkvid            - Video streams junctions will be marked as gap. This option may be useful when joining two files encoded by slightly different versions of codec what may cause artefacts appear on segment junctions.
	-ebkf              - streams will end before nearest past key frame,
	-u                 - makes resulting files unique by changing original ASF file identificators into unique ones,
	-act               - adjust creation time of the file to the time of creation of the original file plus start time.
	-nots              - leaves sample times and packet times unchanged.
	-noindex           - don't index output file,
	-forceindex        - force writting advanced index,
	-sionly            - simple index only,
	-nomarkers         - don't copy markers,
	-noscripts         - don't copy script command,
	-nostr <numbers>   - don't copy selected streams. <numbers> are stream numbers separated by space or comma. This switch can be used many times.
	-q                 - quiet mode - only few information are presented,
	-v                 - verbose mode - turned on by default,
	-details           - stronger verbose mode - shows many details about copying process, among other things key frames,
	-debug             - strongest verbose mode - debug mode,
	-y                 - overwrite without asking,
	-bw <milliseconds> - forces setting of the initial play delay. This value has direct impact on the internal bucket size. Selecting too small value may cause sample losing.
	-ps <bytes>        - forces size of data packets.
	-optps             - sets optimal size of data packets.
	-adelay [-]<time>  - audio delay. Can be negative value,
	-sdelay <number> <time> - stream delay. Can be negative value,
	-info              - just show information on input sources.
	-infokf            - just show information on input sources and locations of key frames in selected time range.
	-infoidx           - show detailed information on indices appended to a processed file. Add -details switch to get additional information on any eventual errors.
	-infohdr           - show detailed information on file header.
	-h                 - show this help screen.
	
	<time> in general is given in seconds, but it accepts following formats as well:
		1:59:45.35 = 1 h, 59 min, 45s, 35 hundredths, 3:30 = 3 min, 30 sec., 1023.101 = 1023 sec. and 101 thousandths, etc.
	<in_file_list> format: - each line contains next file to read/join.
	<segments_list> format: - each line contains one segment description:
		<start_time><separators><duration> e.g.: 14:45, 3:00
	<attrib_list> format: - each line consists of: <attribute_name>=<value>
		The format is similar to the format of *.INI files. Following attributes are available to set:
		Title, Author, Description, Rating, Copyright.
	<marker_list> format: - each line consists of: <time> <marker_name>
	<script_list> format: - each line consists of: 
		<time> <command_type> <command_string>, where command type is "URL" or "FILENAME". Custom types are also allowed.
	
	(*) - those options does not guarantee correct results. While it is highly likely that WMV3, WVC1, WMVA, MP42 and MP43 video formats will be correctly handled, all other formats may not be recognized.
'''


def probe(*args, commands=['-info', '-infohdr']):
	a = AsfBinConverter()
	for filename in args:
		proc = subprocess.Popen([a.executable, '-i', filename]+commands,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE)
		r, _ = a.parse_output(proc.communicate(), returncode=proc.returncode)
		if not r:
			return False
	return True
class AsfBinConverter(ConverterBase):
	@staticmethod
	def match_filenames(*args):
		r = []
		y = r.append
		for arg in args:
			_, ext = os.path.splitext(arg)
			if ext in ( '.ASF', '.WMV' ):
				y(ext)
		return r
	def __init__(self, **kwargs):
		self.dry_run = kwargs.pop('dry_run', None)
		if sys.platform.startswith('win'):
			self.executable = 'ASFBIN.EXE'
		else:
			self.executable = 'asfbin'
		self.extra_options = kwargs
	def get_commands(self, input_filename,
					 output_filename='{filepart}_.WMV',
					 segments_filename='{basename}.AsfBin.segments',
					 **kwargs):
		options = kwargs
		dirname, basename = os.path.split(input_filename)
		filepart, ext = os.path.splitext(basename)
		try:
			output_filename = output_filename.format(**locals())
		except:
			warning( "output_filename={}, which is probably not what you intended".format(output_filename) )
		try:
			segments_filename = segments_filename.format(**locals())
		except:
			warning( "segments_filename={}, which is probably not what you intended".format(segments_filename) )
		commands = options.pop('commands', [ '-sep' ])+['-o', output_filename ]
		if 'title' in options or 'attributes' in options:
			a = options.pop('attributes', {})
			if 'title' in options:
				a['Title'] = options.pop('title')
			attributes_filename = basename+'.AsfBin.attributes'
			with open(attributes_filename, 'w') as ofo:
				for k, v in attributes.items():
					ofo.write('{}={}\n'.format(k.title(), v))
			commands += [ '-a', attributes_filename ]
		if 'splits' in options:
			'''AsfBin takes (timestamp, duration) instead of (timestamp, timestamp)'''
			my_pairs = [ (b, Decimal(e)-Decimal(b)) for (b, e) in options.pop('splits') ]
			with open(segments_filename, 'w') as ofo:
				for b, d in my_pairs:
					ofo.write('{}, {}\n'.format(b, d))
			commands += [ '-s', segments_filename ]
		if 'frames' in options:
			raise NotImplementedError()
		if 'chapters' in options: # these are pairs
			markers_filename = basename+'.AsfBin.markers'
			with open(markers_filename, 'w') as ofo:
				for t, n in options.pop(chapters):
					ofo.writeline('{} {}\n'.format(t, n))
			commands += [ '-m', markers_filename ]
		for k, v in options.items():
			debug("Extra parameter unused: {}={}".format(k, v))
		# AsfBin is picky about this order:
		return [ [ asfbin_executable, '-i', input_filename ]+commands ]
	def parse_output(self, streams, **kwargs):
		stdout_contents, _ = streams
		debug( "{:,}B of stdout".format(len(stdout_contents)) )
		for b in stdout_contents.split(b'\n'):
			parse_line(b)
		return kwargs.pop('returncode', 0) == 0, []
def parse_line(b,
			   prefix='STDOUT',
			   progress=print if sys.stdout.isatty() else (lambda x: None),
			   encoding='ASCII'):
	line = b.decode(encoding).rstrip()
	if line.startswith('0-100%:'): # progress
		#return line
		progress(line)
		return
	for text in errors:
		if text in line:
			raise AsfBinException(line)
			break
	else:
		debug(prefix+' '+line)

if sys.platform.startswith('win'):
	asfbin_executable = 'ASFBIN.EXE'
else:
	asfbin_executable = 'asfbin'
debug("AsfBin is {}".format(asfbin_executable))

def AsfBin_command(input_filename, output_filename='', segments_filename='', **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not segments_filename:
		segments_filename = basename+'.AsfBin.segments'
	commands = kwargs.pop('commands', [ '-sep' ])
	if not output_filename:
		#output_filename = filepart+'_{000}'+'.WMV' # buggy?
		output_filename = filepart+'_'+'.WMV'
	commands += ['-o', output_filename ]
	if 'title' in kwargs or 'attributes' in kwargs:
		a = kwargs.pop('attributes', {})
		if 'title' in kwargs:
			a['Title'] = kwargs.pop('title')
		attributes_filename = basename+'.AsfBin.attributes'
		with open(attributes_filename, 'w') as ofo:
			for k, v in attributes.items():
				ofo.write('{}={}\n'.format(k.title(), v))
		commands += [ '-a', attributes_filename ]
	if 'splits' in kwargs:
		'''AsfBin takes (timestamp, duration) instead of (timestamp, timestamp)'''
		my_pairs = [ (b, Decimal(e)-Decimal(b)) for (b, e) in kwargs.pop('splits') ]
		with open(segments_filename, 'w') as ofo:
			for b, d in my_pairs:
				ofo.write('{}, {}\n'.format(b, d))
		commands += [ '-s', segments_filename ]
	if 'frames' in kwargs: # TODO
		raise NotImplementedError()
	if 'chapters' in kwargs: # these are pairs
		markers_filename = basename+'.AsfBin.markers'
		with open(markers_filename, 'w') as ofo:
			for t, n in kwargs.pop(chapters):
				ofo.writeline('{} {}\n'.format(t, n))
		commands += [ '-m', markers_filename ]
	for k, v in kwargs.items():
		debug("Extra parameter unused: {}={}".format(k, v))
	# AsfBin is picky about this order:
	return [ asfbin_executable, '-i', input_filename ]+commands
def parse_output(out, err='', returncode=None):
	errors = [ 'PROCESSING FAILED', 'At least one file cannot be processed', 'exists but it is too short' ]
	def parse_line(b, prefix='STDOUT', encoding='ASCII'):
		line = b.decode(encoding).rstrip()
		for text in errors:
			if text in line:
				raise AsfBinException(line)
				break
		if line.startswith('0-100%:'): # progress
			return line
		else:
			debug(prefix+' '+line)
	#for b in err.splitlines(): # AsfBin doesn't use stderr
	#	parse_line(b, prefix='STDERR')
	for b in out.splitlines():
		parse_line(b)
	return returncode or 0
### EOF
