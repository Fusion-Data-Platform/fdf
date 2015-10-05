# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 11:18:16 2015

@author: ktritz
"""
import os

#if 'linux' in os.sys.platform:
#    FDF_DIR = './fdf/'
#elif 'win32' in os.sys.platform:
#    FDF_DIR = '.\\fdf\\'

# fixed bug where fdf crashed with script outside of fdf directory (DRS 10/5/15)
FDF_DIR = os.path.dirname(os.path.abspath(__file__))

# is FDF_MDS_SERVER used anywhere  -ds 8/9/15
#FDF_MDS_SERVER = 'skylark.pppl.gov:8501'
