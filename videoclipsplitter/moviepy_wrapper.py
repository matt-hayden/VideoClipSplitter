#! /usr/bin/env python3
import os.path

import moviepy.editor

from . import ConverterBase, SplitterException

class moviepyException(SplitterException):
	pass

def moviepy_wrapper(input_filename, output_file_pattern='', **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	if not output_file_pattern:
		output_file_pattern = filepart+'_{:d}'+ext
	#if 'title' in kwargs or 'attributes' in kwargs: # ...
	if 'splits' in kwargs:
		vfc = moviepy.editor.VideoFileClip(input_filename)
		for n, (b, e) in enumerate(kwargs.pop('splits')):
			sc = vfc.subclip(b, e)
			sc.write_videofile(output_file_pattern.format(n), **kwargs)
	# frames and chapters could go here
# probe method could go here

