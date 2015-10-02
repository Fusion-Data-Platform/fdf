# -*- coding: utf-8 -*-
"""
@author: drsmith-wisc
"""

from os import getenv
import pymssql
import numpy as np

server = 'sql2008.pppl.gov\sql2008'
username = getenv('USER') or getenv('USERNAME')
password = 'pfcworld'
database = 'nstxlogs'
port = '62917'

try:
    connection = pymssql.connect(server=server, user=username,
                                 password=password, database=database,
                                 port=port, as_dict=True)
except:
    connection = pymssql.connect(server=server, user='drsmith',
                                 password=password, database=database,
                                 port=port, as_dict=True)

shot_query_prefix = ('SELECT username, rundate, shot, xp, topic, text, entered, voided '
                     'FROM entries '
                     'WHERE voided IS null')

shotlist_query_prefix = ('SELECT DISTINCT rundate, shot, xp, voided '
                         'FROM entries '
                         'WHERE voided IS null')


def iterable(obj):
    try:
        iter(obj)
        if type(obj) is str:
            return False
        return True
    except TypeError:
        return False


def get_shotlist(rundate=[], xp=[], verbose=False):
    cursor = connection.cursor()
    cursor.execute('SET ROWCOUNT 80')

    shotlist = []   # start with empty shotlist
    rundate_list = rundate
    if not iterable(rundate_list):      # if it's just a single date
        rundate_list = [rundate_list]   # put it into a list
    for rundate in rundate_list:
        query = ('{} and rundate={} ORDER BY shot ASC'.
                 format(shotlist_query_prefix, rundate))

        cursor.execute(query)

        rows = cursor.fetchall()
        if verbose:
            print('Rundate {}'.format(rundate))
            for row in rows:
                print('   {} in XP {}'.format(row['shot'], row['xp']))
        shotlist.extend([row['shot'] for row in rows  # add shots to shotlist
                        if row['shot'] is not None])

    xp_list = xp
    if not iterable(xp_list):           # if it's just a single xp
        xp_list = [xp_list]             # put it into a list
    for xp in xp_list:
        query = ('{} and xp={} ORDER BY shot ASC'.
                 format(shotlist_query_prefix, xp))

        cursor.execute(query)

        rows = cursor.fetchall()
        if verbose:
            print('XP {}'.format(xp))
            for row in rows:
                print('   {} on rundate {}'.
                      format(row['shot'], row['rundate']))
        shotlist.extend([row['shot'] for row in rows  # add shots to shotlist
                        if row['shot'] is not None])

    cursor.close()
    return np.unique(shotlist)


def get_shotlist_from_date(rundate):

    cursor = connection.cursor()
    cursor.execute('SET ROWCOUNT 80')

    query = ('{} and rundate={} '
             'ORDER BY shot ASC'.format(shotlist_query_prefix, rundate))

    cursor.execute(query)

    rows = cursor.fetchall()
    print('Rundate {}'.format(rundate))
    for row in rows:
        print('   {} in XP {}'.format(row['shot'], row['xp']))

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


if __name__ == '__main__':
    do_shot_query(140001)