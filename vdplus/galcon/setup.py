#!/usr/bin/env python3

from setuptools import setup

__version__ = '1.14'

setup(name='visidata-galcon',
      version=__version__,
      install_requires=['visidata@git+https://github.com/saulpw/visidata.git@develop', 'requests'],
      description='Galactic Conquest in VisiData',
      author='Saul Pwanson',
      author_email='vdgalcon@saul.pw',
      url='http://visidata.org/plus/galcon',
      download_url='https://visidata.org/plus/galcon.py',
      scripts=['galcon.py', 'galcon-server.py'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Environment :: Console :: Curses',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Office/Business :: Financial :: Spreadsheet',
      ],
      keywords=('console game textpunk visidata galactic conquest galcon')
      )
