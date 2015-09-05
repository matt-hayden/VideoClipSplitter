#!/usr/bin/env python3
### should you need logging:
#from Splitter import debug, info, warning, error, panic

from Splitter.FFmpeg import *
from Splitter.splits_tsv import *
from Splitter.cli import run

input_file, all_cuts = 'movie.avi', old_splits_file('selected.splits').cuts
print("Loaded {} cuts".format(len(all_cuts) ) )
my_cuts = all_cuts

# crop dimensions can be estimated using the cropdetect video filter
run(input_file, splits=my_cuts, output_ext='.MKV', converter=ffmpeg, filters=['-vf', 'crop=720:352'])
# this is a front-end for:
#ffmpeg(input_file, splits=my_cuts, output_ext='.MKV', filters=['-vf', 'crop=720:352'])
