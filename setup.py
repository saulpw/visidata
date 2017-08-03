#!/usr/bin/env python3

from setuptools import setup

__version__ = '0.1'

setup(name='vgit',
      version=__version__,
      install_requires='visidata>=0.94 sh'.split(),
      description='a sleek terminal user interface for git',
      #long_description=open('README.md').read(),
      author='Saul Pwanson',
      author_email='vgit@saul.pw',
      url='http://github.com/saulpw/vgit',
      download_url='https://github.com/saulpw/vgit/tarball/' + __version__,
      scripts=['vgit'],
      py_modules = ['vgit'],
      license='GPLv3',
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
      keywords=('console textpunk git version-control'
                'curses visidata tui terminal'),
      packages=[''],
      )
