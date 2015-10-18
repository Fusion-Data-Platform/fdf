# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='fdf',
      version = '0.0.1',
      description=['A data access, visualization, and management framework '
          'for magnetic fusion experiments'],
      packages=['fdf'],
      author="John Schmitt, David R. Smith, Kevin Tritz, and Howard Yuh",
      url="https://github.com/Fusion-Data-Framework/fdf",
      requires=['pymysql>=0.6.6'],
      )

