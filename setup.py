#!/usr/bin/env python3

from setuptools import setup
# tox can't actually run python3 setup.py: https://github.com/tox-dev/tox/issues/96
#from visidata import __version__
__version__ = '0.61'

setup(name='visidata',
      version=__version__,
      install_requires='python-dateutil openpyxl'.split(),
      description='curses interface for exploring and arranging tabular data',
      long_description=open('README.md').read(),
      author='Saul Pwanson',
      author_email='vd@saul.pw',
      url='http://github.com/saulpw/visidata',
      download_url='https://github.com/saulpw/visidata/tarball/' + __version__,
      test_suite='visidata.tests',
      scripts=['bin/vd'],
      py_modules = ['visidata'],
      license='GPLv3',
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
      keywords=('console tabular data spreadsheet viewer textpunk'
                'curses csv hdf5 h5 xlsx'),
      packages=['visidata', 'visidata.addons'],
      )
