import os.path


import logging
logger = logging.getLogger('' if __name__ == '__main__' else __name__)
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical

from .namespace import Namespace


class Cut(Namespace):
	'''
	A cut has should have the following members:
		start
		end
		duration
		filename
	Optionally:
		name
		order
		file_duration (some cutting programs cannot accurately determine the end)
	'''
	@property
	def start(self):
		return self.get('start-time', 0)
	@property
	def end(self):
		return self.get('stop-time', 0)
	@property
	def duration(self):
		return float(self['stop-time']) - float(self['start-time'])
	@property
	def name(self):
		"""
		Filenames starting with this path are fixed
		"""
		if True:
			_, basename = os.path.split(self['entry_name'])
			while basename and basename.endswith('(2)'):
				basename = basename[:-3]
			return basename
		else:
			dirname, basename = os.path.split(self['filename'])
			if self['entry_name'].upper().startswith(basename.upper()):
				return self['entry_name'][len(basename):] or self['entry_name']
			else: return self['entry_name']

def _parse(filename):
	with open(filename) as fi:
		numbered_lines = [(NR, line.rstrip()) for NR, line in enumerate(fi)]
	header = ''
	while not header.startswith('#EXTM3U'):
		NR, header = numbered_lines.pop(0)
	number_cuts = 0
	cut = Cut(order=number_cuts)
	for NR, line in numbered_lines:
		if line:
			if line.startswith('#EXTINF'):
				_, text = line.split(':', 1)
				assert 'file_duration' not in cut
				if ',' in text:
					#cut['file_duration'], cut['entry_name'] = file_duration = text.split(',')
					cut['file_duration'], cut['entry_name'] = text.split(',', 1)
				else:
					cut['file_duration'] = text
			elif line.startswith('#EXTVLCOPT'):
				_, text = line.split(':', 1)
				if '=' in text:
					attrib, value = text.split('=', 1)
				assert attrib not in cut
				if attrib == 'stop-time':
					# VLC bugs
					try:
						assert 0 < float(value)
					except:
						error("Illegal {attrib}={value} ignored".format(**locals()))
						continue
				cut[attrib] = value
			elif line.startswith('#'):
				warning("Line {NR} ignored".format(**locals()))
				info("Unrecognized comment or metadata: "+line)
			else:
				cut['filename'] = line
			### Checks on crazy file durations
				if 60*60*12 < float(cut['file_duration']):
					cut['file_duration'] = None
			###
			if 'filename' in cut:
				if not 'start-time' in cut and 'stop-time' in cut:
					cut['start-time'] = '0'
				elif 'start-time' in cut and not 'stop-time' in cut:
					cut['stop-time'] = cut['file_duration']
				yield cut
				number_cuts += 1
				cut = Cut(order=number_cuts)
def extended_m3u_file(*args, **kwargs):
	return list(_parse(*args, **kwargs))
