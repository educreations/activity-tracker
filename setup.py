from setuptools import setup, find_packages

import activity_tracker

setup(
    name='activity-tracker',
    version=activity_tracker.__version__,
    description='DAU/MAU tracker',
    long_description='A library to perform daily-active-user (and similar) tracking',
    packages=find_packages(),
    install_requires=[
        # redis backend requires 'redis'
    ],
    author='Matthew Eastman',
    author_email='matt@educreations.com',
    url='https://github.com/educreations/activity-tracker',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ],
)
