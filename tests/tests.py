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

import unittest as UT
import fdf

class TestParseTree(UT.TestCase):
    """
    """
    
    def setup(self):
        nstx = fdf.Machine('nstx')
        self.shot = nstx.s141000
        
    def testParseTree(self):
        """
        Under machine.shot, ensure every container has a signal, every
        signal has an axis, and every signal has callable plot method
        """
        for attribute in dir(self.shot):
            diagnostic = getattr(self.shot, attribute)
            # ensure every obj under shot is a container
            self.assertIs(isContainer(diagnostic), True, 
                          '{} is not a container'.format(type(diagnostic)))
            self.parseContainer(diagnostic)

    def parseContainer(self, ctnr):
        containsSignal = False
        for attr in dir(ctnr):
            obj = getattr(ctnr, attr)
            if isSignal(obj):
                containsSignal = True # set True when ctnr contains Signal
                containsAxis = False
                containsPlot = False
                for signalAttr in dir(obj):
                    signalObj = getattr(obj, signalAttr)
                    if isAxis(signalObj):
                        # set True when Signal contains Axis
                        containsAxis = True
                if callable(obj.plot):
                    # set True when plot is callable method for Signal
                    containsPlot = True
                self.assertIs(containsAxis, True, 
                              '{} does not contain an axis'.format(type(obj)))
                self.assertIs(containsPlot, True,
                              '{} does not contain plot method'.format(type(obj)))
            if isContainer(obj):
                self.parseContainer(obj)
        self.assertIs(containsSignal, True, 
                      '{} does not contain a signal'.format(type(ctnr)))


def isContainer(obj):
    return issubclass(obj, fdf.factory.Container)

def isSignal(obj):
    return issubclass(obj, fdf.fdf_signal.Signal) and ('Signal' in repr(type(obj)))

def isAxis(obj):
    return issubclass(obj, fdf.fdf_signal.Signal) and ('Axis' in repr(type(obj)))
