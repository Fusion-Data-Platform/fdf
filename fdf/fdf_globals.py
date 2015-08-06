# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 11:18:16 2015

@author: ktritz
"""
import os

if 'linux' in os.sys.platform:
    FDF_DIR = '/p/fdf/fdf/'
elif 'win32' in os.sys.platform:
    FDF_DIR = '.\\fdf\\'

FDF_MDS_SERVER = 'skylark.pppl.gov:8501'
