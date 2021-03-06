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
    Test fixture for shot objects
    """
    
    def setUp(self):
        """
        Setup method for text cases
        """
        nstx = fdf.Machine('nstx')
        self.shot = nstx.s141000

    def testContainer(self, container=None):
        """
        Test case to ensure every containter contains at least a signal
        or subcontainer
        """
        if not container:
            container = self.shot
        validContainer = False
        # test: container contains signal or sub-container
        for attrName in dir(container):
            if attrName == 'ip' or attrName == 'vloop' or attrName == 'equilibria':
                continue
            self.assertIs(hasattr(container, attrName), True,
                          '{} in dir({}) is not a valid attr'.format(attrName, container))
            attr = getattr(container, attrName)
            if isContainer(attr):
                validContainer = True
                self.testContainer(attr)
            if isSignal(attr):
                validContainer = True
        self.assertIs(validContainer, True, 
                      '{} is not a valid container'.format(type(container)))
        
    def testSignalAxes(self, container=None):
        """
        Test case to validate signal axes
        """
        if not container:
            container = self.shot
        for attrName in dir(container):
            if attrName == 'ip' or attrName == 'vloop' or attrName == 'equilibria':
                continue
            self.assertIs(hasattr(container, attrName), True,
                          '{} in dir({}) is not a valid attr'.format(attrName, container))
            attr = getattr(container, attrName)
            if isContainer(attr):
                self.testSignalAxes(attr)
            if isSignal(attr):
                # test: signal contains axes attribute
                self.assertIs(hasattr(attr, 'axes'), True, 
                    '{} in {} does not contain axes attribute'.format(attrName, container))
                axes = attr.axes
                # test: axes elements are axis objects
                for axisName in axes:
                    axis = getattr(attr, axisName)
                    self.assertIs(isAxis(axis), True, 
                        '{} in {} in {} is not an axis'.format(axisName, attrName, container))
                # test: all axis objects are elements in axes attribute
                # test: signal contains at least 1 axis attribute
                containsAxis = False
                for sigAttrName in dir(attr):
                    sigAttr = getattr(attr, sigAttrName)
                    if isAxis(sigAttr):
                        containsAxis = True
                        self.assertIn(sigAttrName, axes, 
                            '{} in {} in {} is an axis not listed in axes attr'.format(sigAttrName, attrName, type(container)))
                self.assertIs(containsAxis, True, 
                    '{} in {} does not contain an axis attribute'.format(attrName, container))

    def testSignalPlotMethod(self, container=None):
        """
        Test case to ensure signal objects contain plot methods
        """
        if not container:
            container = self.shot
        for attrName in dir(container):
            if attrName == 'ip' or attrName == 'vloop' or attrName == 'equilibria':
                continue
            self.assertIs(hasattr(container, attrName), True,
                          '{} in dir({}) is not a valid attr'.format(attrName, container))
            attr = getattr(container, attrName)
            if isContainer(attr):
                self.testSignalPlotMethod(attr)
            if isSignal(attr):
                # test: signal possesses plot method
                self.assertIs(callable(attr.plot), True, 
                    '{} in {} does not possess plot method'.format(attrName, container))
    
    def testSignalTimeAttribute(self, container=None):
        """
        Test case to ensure all signals possess a 'time' attribute
        """
        if not container:
            container = self.shot
        for attrName in dir(container):
            if attrName == 'ip' or attrName == 'vloop' or attrName == 'equilibria':
                continue
            self.assertIs(hasattr(container, attrName), True,
                          '{} in dir({}) is not a valid attr'.format(attrName, container))
            attr = getattr(container, attrName)
            if isContainer(attr):
                self.testSignalTimeAttribute(attr)
            if isSignal(attr):
                # test: signal possesses time attribute
                self.assertIs(hasattr(attr, 'time'), True, 
                    '{} in {} does not possess time attribute'.format(attrName, container))


def isContainer(obj):
    return issubclass(obj.__class__, fdf.factory.Container) and 'Container' in repr(type(obj))

def isSignal(obj):
    return issubclass(obj.__class__, fdf.fdf_signal.Signal) and 'Signal' in repr(type(obj))

def isAxis(obj):
    return issubclass(obj.__class__, fdf.fdf_signal.Signal) and 'Axis' in repr(type(obj))

if __name__ == '__main__':
    unittest.main()
    