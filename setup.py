#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages

import activity_tracker


if sys.argv[-1] == 'publish':
    os.system('python setup.py register sdist bdist_wheel upload')
    sys.exit()


setup(
    name='activity-tracker',
    version=activity_tracker.__version__,
    description='DAU/MAU tracker',
    long_description='A library to perform daily-active-user (and similar) '
                     'tracking',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        # redis backend requires 'redis'
    ],
    tests_require=[
        'fakeredis',
        'nose>=1.0',
        'redis',
    ],
    author='Matthew Eastman',
    author_email='matt@educreations.com',
    url='https://github.com/educreations/activity-tracker',
    license='MIT',
    test_suite='tests',
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ],
)
