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

# base class for declarative class definitions
Base = declarative_base()

# mysql-python is the default DBAPI for the mysql dialect in sqlalchemy
engine = create_engine('mysql+mysqldb://drsmith:pfcworld@sql2008.pppl.gov<:port>/<dbname>')

# generate new Session class for conversing with database
Session = sessionmaker(bind=engine)

