#!/usr/bin/env python3
from decimal import Decimal
import os.path
import string
import subprocess
import sys

from . import *

if sys.platform.startswith('win'):
	asfbin_executable = 'ASFBIN.EXE'
else:
	asfbin_executable = 'asfbin'

class AsfBinException(SplitterException):
	pass

def AsfBin_command(input_filename, output_file_pattern='', segments_filename='', **kwargs):
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
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not segments_filename:
		segments_filename = basename+'.AsfBin.segments'
	commands = kwargs.pop('commands', [ '-sep' ])
	if not output_file_pattern:
		#output_file_pattern = filepart+'_{000}'+'.WMV' # buggy?
		output_file_pattern = filepart+'_'+'.WMV'
	commands += ['-o', output_file_pattern ]
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
	if 'frames' in kwargs:
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
def AsfBin_probe(filename, commands=['-info', '-infohdr']):
	proc = subprocess.Popen([ asfbin_executable, '-i', filename]+commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate()
	return not parse_output(out, err, proc.returncode)
def parse_output(out, err='', returncode=None):
	def _parse(b, prefix='STDOUT', encoding='ASCII'):
		line = b.decode(encoding).rstrip()
		if 'PROCESSING FAILED' in line:
			raise AsfBinException(line)
		elif 'At least one file cannot be processed' in line:
			raise AsfBinException(line)
		elif 'exists but it is too short' in line:
			raise AsfBinException(line)
		elif not line.startswith('0-100%:'): # progress
			debug(prefix+' '+line)
	#for b in err.splitlines(): # AsfBin doesn't use stderr
	#	_parse(b, prefix='STDERR')
	for b in out.splitlines():
		_parse(b)
	return returncode or 0
def asfbin(input_filename, output_file_pattern='', **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not os.path.isfile(input_filename):
		error("Failed to open '{}'".format(input_filename))
		return -1
	debug("Running probe...")
	if not AsfBin_probe(input_filename):
		raise AsfBinExeception("Failed to open '{}'".format(input_filename))
	command = AsfBin_command(input_filename, **kwargs)
	debug("Running "+' '.join(command))
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate()
	return parse_output(out, err, proc.returncode)
