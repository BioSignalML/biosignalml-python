#!/usr/bin/env python

from setuptools import setup, find_packages

version = '0.90'

setup(name='BioSignalML',
      version=version,
      provides=['biosignalml'],
      description='Python BioSignal Abstraction Library',
      author='David Brooks',
      author_email='d.brooks@auckland.ac.nz',
      url='http://www.biosignalml.org/',
      packages=find_packages(exclude=['scope',
                                      'biosignalml.formats.sdf',
                                      'biosignalml.formats.stream',
                                      'biosignalml.formats.unemap',
                                     ]),
     )
