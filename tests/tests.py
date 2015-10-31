# -*- coding: utf-8 -*-
"""
Test module for the FDF package.

https://docs.python.org/2/library/unittest.html

**Usage**::

    % python tests.py

**Test scenarios**

* Verify plot methods for all diagnostic containers and signals
* Verify caching of MDS connections
* Verify correct import of sample diagnostic module
* Verify server pings
* Verify SQL server connection

"""

import unittest
import fdf

class TestShotFixture(unittest.TestCase):
    """
    A test fixture to validate the data structure in shot objects
    """
    
    def setUp(self):
        """
        Setup method for all test cases in this text fixture
        """
        nstx = fdf.Machine('nstx')
        self.shot = nstx.s141000
        
    def testShotCase(self):
        """
        A test case for shot objects to ensure:
        
        * Every containter contains at least a signal or sub-container
        * Every signal contains at least 1 axis
        * Every axis is listed in signal.axes
        * Every item is signal.axes is a valid axis object
        * Every signal possesses a valid plot method
        
        """
        for attrName in dir(self.shot):
            if attrName == 'ip' or attrName == 'vloop':
                continue
            diagnostic = getattr(self.shot, attrName)
            self.assertIs(isContainer(diagnostic), True, 
                          '{} is not a container'.format(type(diagnostic)))
            self.parseContainer(diagnostic, self.shot)

    def parseContainer(self, ctnr, parent=None):
        print('Container: {} under {}'.format(type(ctnr), type(parent)))
        containsSignal = False
        for attrName in dir(ctnr):
            attr = getattr(ctnr, attrName)
            if isSignal(attr):
                containsSignal = True # True when ctnr contains Signal
                axes = attr.axes
                sigAttrNames = dir(attr)
                print('  Signal {} with axes {}'.format(attrName, axes))
                for axis in axes:
                    # loop over axes in signal.axes
                    self.assertIs(isAxis(getattr(attr, axis)), True, 
                                  '{} is not an axis'.format(axis))
                    self.assertIn(axis, sigAttrNames, 
                                  '{} axis is not an attribute'.format(axis))
                containsAxis = False
                for sigAttrName in sigAttrNames:
                    # loop over signal attributes
                    sigAttr = getattr(attr, sigAttrName)
                    if isAxis(sigAttr):
                        containsAxis = True
                        self.assertIn(sigAttrName, axes, 
                                      '{} axis not in Axes'.format(sigAttrName))
                self.assertIs(containsAxis, True, 
                              '{} does not contain an axis'.format(type(attr)))
                containsPlot = False
                if callable(attr.plot):
                    # set True when plot is callable method for Signal
                    containsPlot = True
                    #print('  Plot method name: {}'.format(attr.plot.__name__))
                    #print('  Plot method module: {}'.format(attr.plot.__module__))
                self.assertIs(containsPlot, True,
                              '{} does not contain plot method'.format(type(attr)))
        for attrName in dir(ctnr):
            attr = getattr(ctnr, attrName)
            if isContainer(attr):
                containsSignal = True # true when cntr contains another container
                #print('Sub-container: {}'.format(attrName))
                self.parseContainer(attr, ctnr)
        self.assertIs(containsSignal, True, 
                      '{} does not contain a signal'.format(type(ctnr)))


def isContainer(obj):
    return issubclass(obj.__class__, fdf.factory.Container) and 'Container' in repr(type(obj))

def isSignal(obj):
    return issubclass(obj.__class__, fdf.fdf_signal.Signal) and ('Signal' in repr(type(obj)))

def isAxis(obj):
    return issubclass(obj.__class__, fdf.fdf_signal.Signal) and ('Axis' in repr(type(obj)))

if __name__ == '__main__':
    f = open('test_output.txt', 'w')
    runner = unittest.TextTestRunner(f)
    unittest.main(testRunner=runner)
    f.close()
    