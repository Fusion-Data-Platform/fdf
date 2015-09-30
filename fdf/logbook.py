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

shot_query_prefix = ('SELECT username, rundate, shot, xp, topic, text, entered, voided '
                     'FROM entries '
                     'WHERE voided IS null')

shotlist_query_prefix = ('SELECT DISTINCT rundate, shot, xp, voided '
                    'FROM entries '
                    'WHERE voided IS null')

def get_shotlist_from_date(rundate):
    
    cursor = connection.cursor()
    cursor.execute('SET ROWCOUNT 80')
    
    query = ('%s and rundate=%d '
            'ORDER BY shot ASC'
            % (shotlist_query_prefix, rundate))
    
    cursor.execute(query)
    
    rows = cursor.fetchall()
    print('Rundate %d' % rundate)
    for row in rows:
        print('   %d in XP %d' % (row['shot'], row['xp']))
    
    cursor.close()

def get_shotlist_from_xp(xp):
    
    cursor = connection.cursor()
    cursor.execute('SET ROWCOUNT 80')
    
    query = ('%s and xp=%d '
            'ORDER BY shot ASC'
            % (shotlist_query_prefix, xp))
    
    cursor.execute(query)
    
    rows = cursor.fetchall()
    print('XP %d' % xp)
    for row in rows:
        print('   %d on rundate %d' % (row['shot'], row['rundate']))
    
    cursor.close()

def do_shot_query(shot):
                             
    cursor = connection.cursor()
    cursor.execute('SET ROWCOUNT 80')
    
    query = ('%s and shot=%d '
             'ORDER BY shot ASC, entered ASC' 
             % (shot_query_prefix, shot))
    
    cursor.execute(query)
    
    rows = cursor.fetchall()
    for row in rows:
        print('************************************')
        print(('rundate: %d\n'
            'xp: %d\n'
            'shot: %d\n'
            'author: %s\n'
            'topic: %s\n'
            'entry datetime: %s\n'
            'text: %s\n'
            % (row['rundate'], row['xp'], row['shot'], 
               row['username'], row['topic'], row['entered'], row['text'])))
    
    cursor.close()
