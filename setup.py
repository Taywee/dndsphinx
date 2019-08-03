#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2019 Taylor C. Richberger <taywee@gmx.com>
# This code is released under the license described in the LICENSE file

from setuptools import setup

setup(
    name='dndsphinx',
    version='0.0.1',
    url='https://github.com/Taywee/dndsphinx',
    downnload_url='https://pypi.python.org/pypi/dndsphinx',
    license='GPL3+',
    author='Taylor C. Richberger',
    author_email='taywee@gmx.com',
    description='Sphinx domain for documenting and organizing Dungeons & Dragons campaigns',
    long_description='Sphinx domain for documenting and organizing Dungeons & Dragons campaigns',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=[
        'dndsphinx',
    ],
    install_requires=[
        'Sphinx >= 2.0.0, <3.0.0',
    ],
)
