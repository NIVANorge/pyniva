# -*- coding: utf-8 -*-
"""A setuptools based module for the NIVA tsb module/application.
"""

from setuptools import setup, find_packages


setup(
    name='pyniva',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.2.0',

    description="Python wrapper/API for interacting with NIVA's data platform",

    # The project's main homepage.
    url='https://github.com/NIVANorge/pyniva',

    # Author details
    author='Grunde Løvoll',
    author_email='grunde.loevoll@niva.no',

    # Choose your license
    license='Owned by NIVA',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Data Access :: Time Series',

        # Pick your license as you wish (should match "license" above)
        'License :: Owned by NIVA http://www.niva.no/',
        
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='metadata timeseries data',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['pandas', 'numpy', 'requests', 'pyjwt', 'cryptography'],
    test_suite='tests',
)