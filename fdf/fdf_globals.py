# -*- coding: utf-8 -*-
"""
fdf_globals.py contains package-level constants

Created on Thu Jun 18 11:18:16 2015

@author: ktritz
"""
import os


FDF_DIR = os.path.dirname(os.path.abspath(__file__))
"""Path string: top-level directory for FDF package"""

MDS_SERVERS = {
    'nstx': 'skylark.pppl.gov:8501'
}
"""Dictionary: machine-name key paired to MDS server"""

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
"""Dictionary: machine-name key paired with logbook login credentials"""


class FdfError(Exception):
    """
    Error class for FDF package
    
    Usage
    -----
    raise FdfError('my error message')
    """
    def __init__(self, message=''):
        self.message = message
    def __str__(self):
        return self.message

