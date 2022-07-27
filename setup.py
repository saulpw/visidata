# SPDX-License-Identifier: MIT

from setuptools import setup


exec(open('vdibis/__about__.py').read())


def readme():
    with open("README.md") as f:
        return f.read()


def requirements():
    with open("requirements.txt") as f:
        return f.read().split("\n")


setup(
        name="vdibis",
        version=__version__,
        description=__description__,
        long_description=readme(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3",
        ],
        keywords="visidata ibis apache sql substrait",
        author="Saul Pwanson",
        url="https://github.com/visidata/vdibis",
        python_requires=">=3.8",
        packages=["vdibis"],
        py_modules=["vdibis"],
        entry_points={'visidata.plugins': 'vdibis=vdibis'},
        install_requires=requirements(),
)
