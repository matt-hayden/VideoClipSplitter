#!/usr/bin/env python3
from .AsfBin import asfbin
from .AviDemux import avidemux
from .FFmpeg import ffmpeg
from .MkvMerge import mkvmerge
from .MP4Box import MP4Box

converters = [ mkvmerge, ffmpeg, MP4Box, avidemux, asfbin ] # ordered by general usefulness
default_converter = converters[0] # most capable

