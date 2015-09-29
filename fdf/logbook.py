# -*- coding: utf-8 -*-
"""
@author: drsmith-wisc
"""

from os import getenv
import pymssql

server = 'sql2008.pppl.gov\sql2008'
username = getenv('USER')
password = 'pfcworld'
database = 'nstxlogs'
port = '62917'

connection = pymssql.connect(server=server,
                             user=username,
                             password=password,
                             database=database,
                             port=port)
                             
cursor = connection.cursor()

cursor.execute('SET ROWCOUNT 80')

query = """
select dbkey, username, rundate, shot, xp, topic, text, entered, voided from entries where VOIDED IS NULL and shot=140000 order by Shot asc, Entered asc
"""
cursor.execute(query)

print(cursor.fetchone())
print(cursor.fetchone())

#import pyodbc
#
#driver = 'ODBC for MySQL (64 bit)'
#server = 'sql2008.pppl.gov\sql2008'
#connect_str = ('Driver={%s};'
#    'Server=%s;'
#    'UID=drsmith;'
#    'PWD=pfcworld;'
#    'Database=nstxlogs;'
#    'Port=62917' % (driver, server))
#
#connection = pyodbc.connect(connect_str)
#
#cursor = connection.cursor()

cursor.close()
connection.close()
