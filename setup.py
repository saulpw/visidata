#!/usr/bin/env python3

from setuptools import setup
import os.path
import sysconfig


def all_requirements():
    requirements = []
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if (line and not line.startswith('#') and not line.startswith('-e git+https') and not line.startswith('git+https')):

                # inline comments
                if '#' in line:
                    line = line.split('#')[0].strip()

                if line:
                    requirements.append(line)

        return requirements


# tox can't actually run python3 setup.py: https://github.com/tox-dev/tox/issues/96
# from visidata import __version__
__version__ = "3.4.dev0"
install_requires = [
    "python-dateutil",
    'importlib_resources; python_version<"3.9"',
    'standard-mailcap; python_version>="3.13"',
]

if not sysconfig.get_platform().startswith("mingw"):  # 2757
    install_requires += ['windows-curses >= 2.4.1; platform_system == "Windows"']   # 2119

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
    scripts=["bin/vd2to3.vdx"],
    entry_points={
        "console_scripts": ["vd=visidata.main:vd_cli",
                            "visidata=visidata.main:vd_cli"],
    },
    py_modules=["visidata"],
    install_requires=install_requires,
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
        ("share/man/man1", [f for f in ["visidata/man/vd.1", "visidata/man/visidata.1"] if os.path.exists(f)]),
        ("share/applications", ["visidata/desktop/visidata.desktop"]),
        ("share/metainfo", ["visidata/desktop/org.visidata.VisiData.metainfo.xml"]),
        ("share/icons/hicolor/48x48/apps", ["visidata/desktop/icons/48x48/visidata.png"]),
        ("share/icons/hicolor/32x32/apps", ["visidata/desktop/icons/32x32/visidata.png"]),
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
            "shapely",
            "tabulate",
            "tomli",
            "wcwidth",
            "xport>=3.0,<3.3",
        ],"windows-curses": ['windows-curses >= 2.4.1; platform_system == "Windows"',  # 2119
        ],
        "all": all_requirements(),
    },
    package_data={
        "visidata.man": [f for f in ["vd.1", "vd.txt"] if os.path.exists(os.path.join("visidata", "man", f))],
        "visidata.ddw": ["input.ddw", "regex.ddw"],
        "visidata": ["guides/*.md"],
        "visidata.tests": ["sample.tsv", "benchmark.csv"],
        "visidata.desktop": [
            "visidata.desktop",
            "org.visidata.VisiData.metainfo.xml",
            "icons/48x48/visidata.png",
            "icons/32x32/visidata.png",
        ],
        "visidata.experimenta.noahs_tapestry": [
            "*.ddw",
            "*.md",
            "*.json",
            "noahs.sqlite",
        ],
    },
    license="GPL-3.0-only",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
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
