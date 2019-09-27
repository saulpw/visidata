#!/usr/bin/env python3

from setuptools import setup
__version__ = '0.2-dev'

setup(name='vsh',
      version=__version__,
      description='interactive terminal user interfaces for classic unix tools',
      # we need a README
      long_description='',
      author='Saul Pwanson',
      python_requires='>=3.6',
      author_email='code@saul.pw',
      scripts=['vls', 'vping', 'vtop'],
      # point to our submodule of sh
      # which version of visidata?
      install_requires=['visidata @ git+git://github.com/saulpw/visidata@develop', 'sh @ git+git://github.com/saulpw/sh@master', 'mutagen', 'psutil'],
      license='GPLv3',
      )
