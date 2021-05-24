#!/usr/bin/env python3

from setuptools import setup
__version__ = '0.2-dev'

setup(name='vsh',
      version=__version__,
      description='interactive terminal user interfaces for classic unix tools',
      # we need a README
      long_description=open('README.md').read(),
      install_requires=['visidata @ git+git://github.com/saulpw/visidata@develop', 'sh @ git+git://github.com/saulpw/sh@master', 'mutagen', 'psutil'],
      author='Saul Pwanson',
      author_email='vsh@saul.pw',
      url='https://github.com/saulpw/visidata/vsh',
      scripts=['vls', 'vping', 'vtop'],
      python_requires='>=3.6',
      download_url='https://github.com/saulpw/vsh/tarball/' + __version__,
      license='GPLv3',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Environment :: Console :: Curses',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Information Techonology',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Utilities',
          'Topic :: Terminals',
      ],
      keywords=('console textpunk ls sh top ping curses visidata tui terminal'),
      )
