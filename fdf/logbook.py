# -*- coding: utf-8 -*-
"""
@author: drsmith-wisc
"""

from logbook_globals import Session, Logbook

# open a session
session = Session()

for shot, in session.query(Logbook.shot).filter_by(shot=140000):
    print shot
