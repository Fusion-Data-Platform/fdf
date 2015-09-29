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
                             port=port,
                             as_dict=True)
                             
cursor = connection.cursor()

cursor.execute('SET ROWCOUNT 80')

query_txt = """
select dbkey, username, rundate, shot, xp, topic, text, entered, voided from entries where VOIDED IS NULL and shot=140000 order by Shot asc, Entered asc
"""
cursor.execute(query_txt)

rows = cursor.fetchall()
for row in rows:
    print(('dbkey: %d\n'
        'date: %d\n'
        'xp: %d\n'
        'shot: %d\n'
        'author: %s\n'
        'datetime: %s\n'
        'text: %s\n'
        % (row['dbkey'], row['rundate'], row['xp'], row['shot'], 
            row['username'], row['entered'], row['text'])))

cursor.close()
connection.close()
