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

# changed nstx server to skylark.pppl.gov - ds 9/30/2015
MDS_SERVERS = {
    'nstx': 'skylark.pppl.gov:8501'
}

LOGBOOK_CREDENTIALS = {
    'nstx': {
        'server': 'sql2008.pppl.gov\sql2008',
        'username': os.getenv('USER') or os.getenv('USERNAME'),
        'password': 'pfcworld',
        'database': 'nstxlogs',
        'port': '62917',
        'table': 'entries'
    }
}
