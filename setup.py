# -*- coding: utf-8 -*-
"""A setuptools based module for the NIVA tsb module/application.
"""

from setuptools import setup, find_packages


setup(
    name='pyniva',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.4.0',

    description="Python wrapper/API for interacting with NIVA's data platform",

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
    install_requires=['pandas>=0.24,<1.0', 'numpy>=1.16,<2.0', 'requests>=2.20,<3.0',
                      'pyjwt>=1.7,<2.0', 'cryptography>=2.5,<3.0'],
    test_suite='tests',
)