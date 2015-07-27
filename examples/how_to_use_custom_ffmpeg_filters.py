#!/usr/bin/env python3
### should you need logging:
#from Splitter import debug, info, warning, error, panic

from Splitter.FFmpeg import *
from Splitter.cutlist import *

input_file, all_cuts = 'video.wmv', cutlist('cutlist').cuts
print("Loaded {} cuts".format(len(all_cuts) ) )
my_cuts = [ (cut.start, cut.end) for order, cut in enumerate(all_cuts, start=1) if order in (2,3,8,9) ] # select only certain cuts, for example

for order, (b, e) in enumerate(my_cuts):
	print("Cut {} will be {}-{}, maybe ordered differently than in the cutlist".format(order, b, e))

# crop dimensions can be estimated using the cropdetect video filter
ffmpeg(input_file, splits=my_cuts, ext='.MKV', filters=['-vf', 'crop=720:352'])
