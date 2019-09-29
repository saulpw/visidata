#!/usr/bin/env python3

from setuptools import setup

__version__ = '0.2-dev'

setup(name='vgit',
      version=__version__,
      description='a sleek terminal user interface for git',
      long_description=open('README.md').read(),
      install_requires=['visidata @ git+git://github.com/saulpw/visidata@develop', 'sh @ git+git://github.com/saulpw/sh@master'],
#      long_description=open('README.md').read(),
      author='Saul Pwanson',
      author_email='vgit@saul.pw',
      url='https://github.com/saulpw/visidata/vgit',
      scripts=['../bin/vgit'],
      py_modules = ['amend', 'blame', 'diff', 'git', 'grep', 'overview', 'repo', 'status'],
      license='GPLv3',
      python_requires='>=3.6',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Environment :: Console :: Curses',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Utilities',
          'Topic :: Software Development :: Version Control',
          'Topic :: Terminals'
      ],
      keywords=('console textpunk git version-control curses visidata tui terminal'),
      )
