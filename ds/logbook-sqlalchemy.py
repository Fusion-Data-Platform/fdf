# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 10:24:41 2015

@author: drsmith
"""

from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

Base = automap_base()


dbkeys = dict(servertype='mssql',
              frontend='pymssql',
              server='sql2008.pppl.gov\sql2008',
              username=getenv('USER'),
              password='pfcworld',
              database='nstxlogs',
              port='62917')

connection_str = '%s+%s://%s:%s@%s:%s/%s' % \
    (dbkeys['servertype'], dbkeys['frontend'],
     dbkeys['username'], dbkeys['password'],
     dbkeys['server'], dbkeys['port'],
     dbkeys['database'])
print(connection_str)

engine = create_engine(connection_str, echo=True)

Base.prepare(engine, reflect=True)

LogbookEntry = Base.classes.entries

#session = Session(engine)
#
#
#class LogbookEntry(Base):
#    __tablename__ = 'entries'
#    __table_args__ = {'autoload':True}
#
## generate new Session class for conversing with database
#def loadSession():
#    metadata = Base.metadata
#    Session = sessionmaker(bind=engine)
#    session = Session()
#    return session
#
#if __name__ == '__main__':
#    session = loadSession()
#    res = session.query(LogbookEntry).all()
#    print(res[1].title)



