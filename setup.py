#!/usr/bin/env python3

from setuptools import setup

setup(name="visidata",
      version="0.37",
      description="a curses interface for exploring and arranging tabular data",
      long_description=open('README.md').read(),
      author="Saul Pwanson",
      author_email="vd@saul.pw",
      url="http://saul.pw/visidata",
      download_url="http://saul.pw/vd",
      scripts=['bin/vd'],
      license="GPLv3",
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Environment :: Console :: Curses',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Database :: Front-Ends',
          'Topic :: Scientific/Engineering',
          'Topic :: Office/Business :: Financial :: Spreadsheet',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Utilities',
      ],
      keywords=("console tabular data spreadsheet viewer textpunk"
                "curses csv hdf5 h5 xlsx"),
      )
