#!/usr/bin/env python

from setuptools import setup, find_packages

version = "0.6.0b"


setup(name='BioSignalML',
      version=version,
      provides=['biosignalml'],

      description='Python BioSignal Abstraction Library',
#     keywords = "hello world example examples",
      author='David Brooks',
      author_email='d.brooks@auckland.ac.nz',
      url='https://github.com/dbrnz/biosignalml-corelib',

      license = "ASL",
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Environment :: Web Environment',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering :: Bio-Informatics',
                  ],

      zip_safe = True,
      packages=find_packages(exclude=['biosignalml.formats.sdf',
                                      'biosignalml.formats.stream',
                                      'biosignalml.formats.unemap',
                                     ]),
      install_requires=['distribute',
                        'isodate  >= 0.4.7',
                        'pyparsing >= 1.5.0, < 2.0.0',
                        'httplib2 >= 0.7.7',
                        'python-dateutil >= 2.0',
                        'ws4py >= 0.2.4',
                        'rdflib >= 4.1.0',
                        'pint >= 0.5.1',
                        'numpy >= 1.8.1',
                       ],
      )
