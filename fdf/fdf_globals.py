# -*- coding: utf-8 -*-
"""
Package-level constants and FdfError class
"""

"""
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

def machineAlias(machine):

    ALIASES = {
        'nstx': ['nstx', 'nstxu', 'nstx-u'],
    }
    
    for key, value in iter(ALIASES.items()):
        if machine.lower() in value:
            return key
    txt = '\n{} is not a valid machine.\n'.format(machine)
    txt = txt + 'Valid machines are:\n'
    for machinekey in ALIASES:
        txt = txt + '  {}\n'.format(machinekey.upper())
    raise FdfError(txt)


class FdfError(Exception):
    """
    Error class for FDF package

    **Usage**::

    raise FdfError('my error message')

    """
    def __init__(self, message=''):
        self.message = message

    def __str__(self):
        return self.message
