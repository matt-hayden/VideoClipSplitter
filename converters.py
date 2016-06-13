#!/usr/bin/env python3
from .AsfBin import asfbin
from .AviDemux import avidemux
from .FFmpeg import ffmpeg
from .MkvMerge import mkvmerge
from .gpac import MP4Box

try:
	from .moviepy_wrapper import moviepy_wrapper
	converters = [ mkvmerge, ffmpeg, moviepy_wrapper, MP4Box, avidemux, asfbin ] # edit below as well
except:
	def moviepy_wrapper():
		return NotImplemented
	converters = [ mkvmerge, ffmpeg, MP4Box, avidemux, asfbin ]

default_converter = converters[0] # most capable

