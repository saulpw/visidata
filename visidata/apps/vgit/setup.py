#!/usr/bin/env python3

from setuptools import setup, find_packages

# Note: use `python3 visidata/apps/setup.py install` from the root directory

__version__ = '0.2-dev'

setup(name='vgit',
      version=__version__,
      description='a sleek terminal user interface for git',
      # long_description=open('README.md').read(),
      install_requires=['sh<2'], # visidata
      packages=find_packages(exclude=["tests"]),
      scripts=['vgit'],
      entry_points={'visidata.plugins': 'vgit=visidata.apps.vgit'},
      author='Saul Pwanson',
      author_email='vgit@saul.pw',
      url='https://github.com/saulpw/visidata/vgit',
      license='GPLv3',
      python_requires='>=3.7',
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
