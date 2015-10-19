# -*- coding: utf-8 -*-
"""
Test module for the FDF package.

**Test scenarios**

* Verify plot methods for all diagnostic containers and signals
* Verify caching of MDS connections
* Verify correct import of sample diagnostic module
* Verify server pings
* Verify SQL server connection
* 


"""

import os
import platform
import unittest

class TestMdsServerPing(unittest.TestCase):
    """
    """
    
    def testNstxMdsServer(self):
        
        import fdf
        server = fdf.fdf_globals.MDS_SERVERS['nstx']
        



