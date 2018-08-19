#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import os
from setuptools import setup, find_packages

long_description = ''

if os.path.isfile('__pypit_desc__.rst'):
    with open('__pypit_desc__.rst') as fp:
        long_description = fp.read()

long_description = long_description or ''

setup(
    long_description=long_description,
    packages=find_packages(),
    # auto generated:
    name='anyioc',
    version='0.3.2',
    description='',
    keywords=[],
    author='Cologler',
    author_email='skyoflw@gmail.com',
    url='https://github.com/Cologler/anyioc-python',
    license='MIT License',
    classifiers=[],
    scripts=[],
    entry_points={},
    zip_safe=False,
    include_package_data=True,
    setup_requires=[],
    install_requires=[],
    tests_require=[],
)
