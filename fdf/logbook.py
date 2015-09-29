# -*- coding: utf-8 -*-
"""
@author: drsmith-wisc
"""

import pyodbc

driver = 'ODBC for MySQL (64 bit)'
server = 'sql2008.pppl.gov\sql2008'
connect_str = ('Driver={%s};'
    'Server=%s;'
    'UID=drsmith;'
    'PWD=pfcworld;'
    'Database=nstxlogs;'
    'Port=62917' % (driver, server))

connection = pyodbc.connect(connect_str)

cursor = connection.cursor()


