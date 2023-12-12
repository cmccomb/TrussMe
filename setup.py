# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='trussme',
    version='0.0.1',
    description='Truss construction and analysis',
    long_description="",
    author='Christopher McComb',
    author_email='chris.c.mccomb@gmail.com',
    url='https://github.com/cmccomb/TrussMe',
    packages=find_packages(exclude='tests')
)
