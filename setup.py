#!/usr/bin/env python

from setuptools import setup

schemec_version = '0.0.1'

setup(name='schemec',
      version=schemec_version,
      description='a toy Scheme-to-C compiler',
      author='Eric Siedel, Michael Walter, N Lance Hepler',
      packages=[
        'schemec'
      ],
      package_dir={
        'schemec': 'schemec',
      }
     )
