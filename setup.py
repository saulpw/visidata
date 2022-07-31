# SPDX-License-Identifier: MIT

from setuptools import setup


exec(open('vdarrow/__about__.py').read())


def readme():
    with open("README.md") as f:
        return f.read()


def requirements():
    with open("requirements.txt") as f:
        return f.read().split("\n")


setup(
        name="vdarrow",
        version=__version__,
        description=__description__,
        long_description=readme(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3",
        ],
        keywords="visidata ibis arrow apache sql substrait",
        author="Saul Pwanson",
        url="https://github.com/visidata/vdarrow",
        python_requires=">=3.8",
        packages=["vdarrow"],
        py_modules=["vdarrow"],
        entry_points={'visidata.plugins': 'vdarrow=vdarrow'},
        install_requires=requirements(),
)
