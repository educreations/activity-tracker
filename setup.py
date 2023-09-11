#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages


if sys.argv[-1] == "publish":
    os.system("python setup.py register sdist bdist_wheel upload")
    sys.exit()


setup(
    name="activity-tracker",
    version="0.0.5",
    description="DAU/MAU tracker",
    long_description="A library to perform daily-active-user (and similar) tracking",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        # redis backend requires 'redis'
        "six",
    ],
    tests_require=["activity-tracker[test]"],
    author="Matthew Eastman",
    author_email="matt@educreations.com",
    url="https://github.com/educreations/activity-tracker",
    license="MIT",
    test_suite="tests",
    extras_require={"test": ["pytest", "pytest-django", "fakeredis", "flake8"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
    ],
)
