# SPDX-License-Identifier: MIT

from setuptools import setup


exec(open('vdsql/__about__.py').read())


def readme():
    with open("README.md") as f:
        return f.read()


def requirements():
    with open("requirements.txt") as f:
        return f.read().split("\n")


setup(
        name="vdsql",
        version=__version__,
        description=__description__,
        long_description=readme(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3",
        ],
        keywords="visidata sql rdbms ibis substrait",
        author="Saul Pwanson",
        url="https://github.com/visidata/vdsql",
        python_requires=">=3.8",
        packages=["vdsql"],
        py_modules=["vdsql"],
        scripts=['bin/vdsql'],
        entry_points={'visidata.plugins': 'vdsql=vdsql'},
        install_requires=requirements(),
)
