#!/usr/bin/env python3
import string

common_chapter_spec_element = '''CHAPTER${n}=$timestamp
CHAPTER${n}NAME=$name
'''
def make_chapters_file(chapters, filename):
	t = string.Template(common_chapter_spec_element)
	with open(chapters_filename, 'w') as cfo:
		for n, (name, timestamp) in enumerate(chapters):
			cfo.write(t.substitute(locals()))
	return True
