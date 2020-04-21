#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Set up module for FileSnitch
Run `python setup.py sdist upload` to publish
"""

import os.path
from setuptools import setup, find_packages

CWD = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(CWD, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

import filesnitch

# packages is empty for this because filesnitch is a flat file. We're using py_modules instead
packages = find_packages(exclude=['contrib', 'docs', 'tests'])  # py module name
package_data = {}
requires = []
classifiers = [
    # See https://pypi.org/classifiers/
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    "Operating System :: OS Independent",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

setup(
    name = 'filesnitch',
    version = filesnitch.__version__,

    description = 'Snitch up multipart files as one read-only file object',
    long_description = long_description,
    long_description_content_type = 'text/markdown',

    author = filesnitch.__author__,
    author_email = filesnitch.__author_email__,

    # Look for package directories automatically
    packages = packages,
    py_modules = ['filesnitch'],
    package_data = package_data,

    # runtime dependencies
    install_requires = requires,
    url = "https://github.com/righthandabacus/filesnitch",
    license = "LGPL",
    classifiers = classifiers,
)
