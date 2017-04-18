from setuptools import find_packages, setup

setup(name='videoclipsplitter',
      use_vcs_version=True,
      description="Wrappers for free cli programs that clip video files",
      url='https://github.com/matt-hayden/VideoClipSplitter',
	  maintainer="Matt Hayden",
	  maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(),
	  install_requires = [
	    "tqdm >= 4.10",
      ],
	  entry_points = {
	    'console_scripts': [
		  'VideoClipSplitter=videoclipsplitter.cli:main',
		],
	  },
      zip_safe=True,
	  setup_requires = [ "setuptools_git >= 1.2", ]
     )
