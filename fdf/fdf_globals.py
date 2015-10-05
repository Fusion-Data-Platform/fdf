# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 11:18:16 2015

@author: ktritz
"""
import os


FDF_DIR = os.path.dirname(os.path.abspath(__file__))

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

