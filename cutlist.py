#! /usr/bin/env python
from decimal import Decimal
from configparser import ConfigParser

from .namespace import Namespace

class IniParser(ConfigParser):
	def contents(self):
		for s in self.sections():
			yield s, Namespace(self.items(section=s))
class CaseSensitiveConfigParser(IniParser):
	optionxform = str

class Cut(Namespace):
	@property
	def end(self):
		return self.start+self.duration

class CutListParser(IniParser):
	cut_factory = Cut
	@property
	def version(self):
		return self.get('General', 'version')
	@property
	def video_filename(self):
		return self.get('General', 'ApplyToFile').strip()
	@property
	def output_name(self):
		return self.get('Info', 'SuggestedMovieName').strip()
	@property
	def cut_sections(self):
		sections = [ s for s in self.sections() if s.startswith('Cut') ]
		return sections
	def _cuts(self):
		for order, section in enumerate(self.cut_sections):
			yield self.cut_factory(
				start=Decimal(self.get(section, 'Start')),
				duration=Decimal(self.get(section, 'Duration')),
				filename=self.video_filename,
				order=order)
	@property
	def cuts(self):
		return list(self._cuts())
#
def cutlist(filename, **kwargs):
	c = CutListParser(**kwargs)
	c.read(filename)
	return c
