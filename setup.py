#!/usr/bin/env python

from setuptools import setup, find_packages

version = '0.3.0'

setup(name='BioSignalML',

      version=version,

      provides=['biosignalml'],

      description='Python BioSignal Abstraction Library',

      author='David Brooks',
      author_email='d.brooks@auckland.ac.nz',
      url='http://www.biosignalml.org/',

#    license = "PSF",
#    keywords = "hello world example examples",

      zip_safe = True,

      packages=find_packages(exclude=['biosignalml.formats.sdf',
                                      'biosignalml.formats.stream',
                                      'biosignalml.formats.unemap',
                                     ]),
      install_requires=['isodate  >= 0.4.7',
                        'pyparsing == 1.5.7',
                        'httplib2 >= 0.7.2',
                        'python-dateutil >= 2.0',
                        'h5py >= 2.0.1',
                        'ws4py >= 0.2.4',
##                        'docutils >= 0.3',  ## For ReST documentation
                        ],
      )
