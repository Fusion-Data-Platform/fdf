# -*- coding: utf-8 -*-
"""
@author: drsmith-wisc
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

# tutorial: http://docs.sqlalchemy.org/en/rel_1_0/orm/tutorial.html
# examples: http://docs.sqlalchemy.org/en/rel_1_0/orm/examples.html

# mysql-python is the default DBAPI for the mysql dialect in sqlalchemy
engine = create_engine('mysql+pymysql://drsmith:pfcworld@sql2008.pppl.gov:62917/logbook')

# base class for declarative class definitions
Base = declarative_base()

class Logbook(Base):
    __tablename__ = 'logbook'
    
    shot = Column(Integer, primary_key=True)
    xp = Column(String(16))
    datetime = Column(String(32), primary_key=True)
    author = Column(String(20), primary_key=True)
    entry = Column(String(256))

# generate new Session class for conversing with database
Session = sessionmaker(bind=engine)

