#!/usr/bin/env python3

from setuptools import setup

# tox can't actually run python3 setup.py: https://github.com/tox-dev/tox/issues/96
# from visidata import __version__
__version__ = "3.2dev"

setup(
    name="visidata",
    version=__version__,
    description="terminal interface for exploring and arranging tabular data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Saul Pwanson",
    python_requires=">=3.8",
    author_email="visidata@saul.pw",
    url="https://visidata.org",
    download_url="https://github.com/saulpw/visidata/tarball/" + __version__,
    scripts=["bin/vd", "bin/vd2to3.vdx"],
    entry_points={
        "console_scripts": ["visidata=visidata.main:vd_cli"],
    },
    py_modules=["visidata"],
    install_requires=[
        "python-dateutil",
        'windows-curses >= 2.4; platform_system == "Windows"',  # 2119
        "importlib-metadata >= 3.6",
        'importlib_resources; python_version<"3.9"',
    ],
    packages=[
        "visidata",
        "visidata.loaders",
        "visidata.vendor",
        "visidata.tests",
        "visidata.guides",
        "visidata.ddw",
        "visidata.man",
        "visidata.themes",
        "visidata.features",
        "visidata.experimental",
        "visidata.experimental.noahs_tapestry",
        "visidata.apps",
        "visidata.apps.vgit",
        "visidata.apps.vdsql",
        "visidata.desktop",
    ],
    data_files=[
        ("share/man/man1", ["visidata/man/vd.1", "visidata/man/visidata.1"]),
        ("share/applications", ["visidata/desktop/visidata.desktop"]),
    ],
    extras_require={
        "test": [
            "brotli",
            "dnslib",
            "dpkt",
            "fecfile",
            "Faker",
            "h5py",
            "lxml",
            "msgpack",
            "odfpy",
            "openpyxl",
            "pandas>=1.5.3",
            "pyarrow",
            "pyconll",
            "pypng",
            "pytest",
            "PyYAML>=5.1",
            "tabulate",
            "tomli",
            "wcwidth",
            "xport>=3.0",
        ]
    },
    package_data={
        "visidata.man": ["vd.1", "vd.txt"],
        "visidata.ddw": ["input.ddw", "regex.ddw"],
        "visidata": ["guides/*.md"],
        "visidata.tests": ["sample.tsv", "benchmark.csv"],
        "visidata.desktop": ["visidata.desktop"],
        "visidata.experimenta.noahs_tapestry": [
            "*.ddw",
            "*.md",
            "*.json",
            "noahs.sqlite",
        ],
    },
    license="GPLv3",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Database :: Front-Ends",
        "Topic :: Scientific/Engineering",
        "Topic :: Office/Business :: Financial :: Spreadsheet",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Utilities",
    ],
    keywords=(
        "console tabular data spreadsheet terminal viewer textpunk"
        "curses csv hdf5 h5 xlsx excel tsv"
    ),
)
