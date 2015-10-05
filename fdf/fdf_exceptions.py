# -*- coding: utf-8 -*-

import fdf_globals

class FdfError(Exception):
    def __init__(self, message=''):
        self.message = message
    def __str__(self):
        return repr(self.message)


class FdfMachineError(FdfError):
    def __init__(self, machine=''):
        txt = 'Unknown machine: {}.'.format(machine.upper())
        txt = txt + '  Available machines are:'
        for machine in fdf_globals.LOGBOOK_CREDENTIALS:
            txt = txt + ' {}'.format(machine.upper())
        self.message = txt

class FdfLogbookError(FdfError):
    def __init__(self, machine='', credentials={}):
        txt = '{} logbook connection failed. '.format(machine.upper())
        txt = txt + 'Server credentials:'
        for key in credentials:
            txt = txt + '  {0}:{1}'.format(key, credentials[key])
        self.message = txt

class FdfLogbookCursorError(FdfError):
    def __init__(self):
        self.message = 'Cursor error'
