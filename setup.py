# -*- coding: utf-8 -*-
"""A setuptools based module for the NIVA tsb module/application.
"""
from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# get the version from the __version__.py file
version_dict = {}
with open(path.join(here, 'pyniva', '__version__.py')) as f:
    exec(f.read(), version_dict)

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyniva',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version_dict['__version__'],

    description="Python wrapper/API for interacting with NIVA's data platform",
    long_description=long_description,
    long_description_content_type='text/markdown',

    # The project's main homepage.
    url='https://github.com/NIVANorge/pyniva',

    # Author details
    author='Zofia Rudjord',
    author_email='zofia.rudjord@niva.no',

    # Choose your license
    license='MIT license',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='metadata timeseries data',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    test_suite='tests',
)