# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 10:38:40 2015

@author: ktritz
"""
import xml.etree.ElementTree as ET
import os
from fdf_globals import *
from fdf_signal import Signal
import numpy as np
import modules
from collections import MutableMapping, OrderedDict
import MDSplus as mds
import types
import inspect
import pymssql

# changed nstx server to skylark.pppl.gov - ds 9/30/2015
mds_servers = {
    'nstx': 'skylark.pppl.gov:8501'
}

logbook_parameters = {
    'nstx': {
        'server': 'sql2008.pppl.gov\sql2008',
        'username': os.getenv('USER') or os.getenv('USERNAME'),
        'password': 'pfcworld',
        'database': 'nstxlogs',
        'port': '62917',
        'table': 'entries'
    }
}

class Machine(MutableMapping):
    '''Factory root class that contains shot objects and MDS access methods.

    Basic class initialization is performed as follows:
    >>>nstx = Machine(name='nstx')

    the Machine class contains a model shot object: nstx.s0

    shot data can be accessed directly through the Machine class:
    >>>nstx.s141398
    >>>nstx.s141399

    alternatively, a list of shot #'s may be provided during initialization:
    >>>nstx = Machine(name='nstx', shotlist=[141398, 141399])

    or added later using the addshot method:
    >>>nstx.addshot([141398, 141399])
    '''

    # Maintain a dictionary of cached MDS server connections to speed up
    # access for multiple shots and trees. This is a static class variable
    # to avoid proliferation of MDS server connections
    _connections = OrderedDict()
    _parent = None

    def __init__(self, name='nstx', shotlist=[], xp=[], date=[]):
        self._shots = {}
        self._classlist = {}
        self._name = name.lower()
        self.s0 = Shot(0, root=self, parent=self)

        if len(self._connections) is 0:
            print('Precaching MDS server connections...')
            for _ in range(2):
                self._connections[mds.Connection(mds_servers[name])] = None
            print('Finished.')
        
        # establish logbook connection
        self._logbook = Logbook(name=self._name, root=self)
        
        # add shots
        if shotlist or xp or date:
            self.addshot(shotlist=shotlist, xp=xp, date=date)

    def __getattr__(self, name):
        try:
            shot = int(name.split('s')[1])
        except:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                                 type(self), name))
        if (shot not in self._shots):
            self._shots[shot] = Shot(shot, root=self, parent=self)
        return self._shots[shot]

    def __repr__(self):
        return '<machine {}>'.format(self._name)

    def __iter__(self):
        # return iter(self._shots.values())
        return iter(self._shots)

    def __contains__(self, value):
        return value in self._shots

    def __len__(self):
        return len(self._shots.keys())

    def __delitem__(self, item):
        self._shots.__delitem__(item)

    def __getitem__(self, item):
        if item == 0:
            return self.s0
        return self._shots[item]

    def __setitem__(self, item, value):
        pass

    def __dir__(self):
        shotlist = ['s0']
        shotlist.extend(['s{}'.format(shot) for shot in self._shots])
        return shotlist

    def _get_connection(self, shot, tree):
        for connection in self._connections:
            if self._connections[connection] == (shot, tree):
                self._connections.pop(connection)
                self._connections[connection] = (shot, tree)
                return connection
        connection, _ = self._connections.popitem(last=False)
        try:
            connection.closeAllTrees()
        except:
            pass
        connection.openTree(tree, shot)
        self._connections[connection] = (shot, tree)
        return connection

    def _get_mdsdata(self, signal):
        # shot = base_container(signal)._parent.shot
        shot = signal.shot
        if shot is 0:
            print('No MDS data exists for model tree')
            return None
        connection = self._get_connection(shot, signal.mdstree)
        data = connection.get(signal.mdsnode)
        try:
            if signal._raw_of is not None:
                data = data.raw_of()
        except:
            pass
        try:
            if signal._dim_of is not None:
                data = data.dim_of()
        except:
            pass
        data = data.value_of().value
        try:
            if signal._transpose is not None:
                data = data.transpose(signal._transpose)
        except:
            pass
        return data

    def _get_modules(self):
        module_dir = os.path.join(FDF_DIR, 'modules')
        modules = [module for module in os.listdir(module_dir)
                   if os.path.isdir(os.path.join(module_dir, module))]
        return modules
        
    def addshot(self, shotlist=[], date=[], xp=[]):
        if not iterable(shotlist):
            shotlist = [shotlist]
        if not iterable(xp):
            xp = [xp]
        if not iterable(date):
            date = [date]
        shots = []
        if shotlist and type(shotlist) is int:
            shots = shots.extend([shotlist])
        if date or xp:
            shots = shots.extend(self._logbook.get_shotlist(date=date, xp=xp))
        for shot in np.unique(shots):
            if shot not in self._shots:
                self._shots[shot] = Shot(shot, root=self, parent=self)
    
    def get_shotlist(self, date=[], xp=[], verbose=False):
        # return a list of shots
        return self._logbook.get_shotlist(date=date, xp=xp, verbose=verbose)
    
    def logbook(self, shot=[], date=[], xp=[]):
        # return a list of logbook entries (dictionaries)
        return self._logbook.get_entries(shot=shot, date=date, xp=xp)
        


#    def _make_logbook_connection(self):
#        # added 9/30/2015 DRS
#        try:
#            self._logbook_connection = pymssql.connect(
#                server=self._lbparams['server'], 
#                user=self._lbparams['username'],
#                password=self._lbparams['password'],
#                database=self._lbparams['database'],
#                port=self._lbparams['port'],
#                as_dict=True)
#        except:
#            print('Connecting to Logbook server as drsmith')
#            self._logbook_connection = pymssql.connect(
#                server=self._lbparams['server'], 
#                user='drsmith',
#                password=self._lbparams['password'],
#                database=self._lbparams['database'],
#                port=self._lbparams['port'],
#                as_dict=True)
#
#
#    def get_shotlist(rundate=[], xp=[], verbose=False):
#        cursor = self._logbook_connection.cursor()
#        cursor.execute('SET ROWCOUNT 200')
#    
#        shotlist = []   # start with empty shotlist
#        rundate_list = rundate
#        if not iterable(rundate_list):      # if it's just a single date
#            rundate_list = [rundate_list]   # put it into a list
#        for rundate in rundate_list:
#            query = ('{} and rundate={} ORDER BY shot ASC'.
#                     format(shotlist_query_prefix, rundate))
#            cursor.execute(query)
#            rows = cursor.fetchall()
#            if verbose:
#                print('Rundate {}'.format(rundate))
#                for row in rows:
#                    print('   {shot} in XP {xp}'.format(**row))
#            shotlist.extend([row['shot'] for row in rows  # add shots to shotlist
#                            if row['shot'] is not None])
#    
#        xp_list = xp
#        if not iterable(xp_list):           # if it's just a single xp
#            xp_list = [xp_list]             # put it into a list
#        for xp in xp_list:
#            query = ('{} and xp={} ORDER BY shot ASC'.
#                     format(shotlist_query_prefix, xp))
#            cursor.execute(query)
#            rows = cursor.fetchall()
#            if verbose:
#                print('XP {}'.format(xp))
#                for row in rows:
#                    print('   {shot} on rundate {rundate}'.format(**row))
#            shotlist.extend([row['shot'] for row in rows  # add shots to shotlist
#                            if row['shot'] is not None])
#    
#        cursor.close()
#        return np.unique(shotlist)
#
#
#    def get_xp_from_date(self, date):
#        # added 9/30/2015 DRS
#        # query logbook on date, return xp list
#        return None
#    
#    def get_date_from_xp(self, xp):
#        # added 9/30/2015 DRS
#        # query logbook on xp, return date list
#        return None


class Logbook():
    
    def __init__(self, name='nstx', root=None):
        self._name = name.lower()
        self._root = root
        self._lbparams = logbook_parameters[self._name]
        self._table = self._lbparams['table']
        self._logbook_connection = None
        self._shotlist_query_prefix = (
            'SELECT DISTINCT rundate, shot, xp, voided '
            'FROM {} WHERE voided IS null').format(self._table)
        self._shot_query_prefix = (
            'SELECT dbkey, username, rundate, shot, xp, topic, text, entered, voided '
            'FROM {} WHERE voided IS null').format(self._table)
        self.logbook = {} # dictionary: kw is shot, value is list of logbook entries
        
        self._make_logbook_connection()

    def _make_logbook_connection(self):
        try:
            self._logbook_connection = pymssql.connect(
                server=self._lbparams['server'], 
                user=self._lbparams['username'],
                password=self._lbparams['password'],
                database=self._lbparams['database'],
                port=self._lbparams['port'],
                as_dict=True)
        except:
            print('Attempting logbook server connection as drsmith')
            try:
                self._logbook_connection = pymssql.connect(
                    server=self._lbparams['server'], 
                    user='drsmith',
                    password=self._lbparams['password'],
                    database=self._lbparams['database'],
                    port=self._lbparams['port'],
                    as_dict=True)
            except:
                print('FDF: cannot connect to {} logbook'.format(self._name.upper()))
                pass

    def _get_cursor(self):
        cursor = None
        try:
            cursor = self._logbook_connection.cursor()
            cursor.execute('SET ROWCOUNT 500')
        except:
            # close connection if possible, then reopen connection and try again
            if hasattr(self._logbook_connection, 'close'): # close connection
                self._logbook_connection.close()
            self._logbook_connection = None
            self._make_logbook_connection()
            try:
                cursor = self._logbook_connection.cursor()
            except:
                print('FDF: cannot initiate cursor for {} logbook'.format(self._name.upper()))
                pass
        return cursor

    def _shot_query(self, shot=[]):
        cursor = self._get_cursor()
        if shot and not iterable(shot):
            shot = [shot]
        for sh in shot:
            if sh not in self.logbook:
                query = ('{0} and shot={1} '
                    'ORDER BY shot ASC, entered ASC'
                    ).format(self._shot_query_prefix, sh)
                cursor.execute(query)
                self.logbook[sh] = cursor.fetchall() # a list of logbook entries
    
    def get_shotlist(self, date=[], xp=[], verbose=False):
        # return list of shots for date and/or XP
        cursor = self._get_cursor()
        shotlist = []   # start with empty shotlist
        
        date_list = date
        if not iterable(date_list):      # if it's just a single date
            date_list = [date_list]   # put it into a list
        for date in date_list:
            query = ('{0} and rundate={1} ORDER BY shot ASC'.
                     format(self._shotlist_query_prefix, date))
            cursor.execute(query)
            rows = cursor.fetchall()
            if verbose:
                print('date {}'.format(date))
                for row in rows:
                    print('   {shot} in XP {xp}'.format(**row))
            shotlist.extend([row['shot'] for row in rows  # add shots to shotlist
                            if row['shot'] is not None])
        
        xp_list = xp
        if not iterable(xp_list):           # if it's just a single xp
            xp_list = [xp_list]             # put it into a list
        for xp in xp_list:
            query = ('{0} and xp={1} ORDER BY shot ASC'.
                     format(self._shotlist_query_prefix, xp))
            cursor.execute(query)
            rows = cursor.fetchall()
            if verbose:
                print('XP {}'.format(xp))
                for row in rows:
                    print('   {shot} on date {rundate}'.format(**row))
            shotlist.extend([row['shot'] for row in rows  # add shots to shotlist
                            if row['shot'] is not None])
        
        cursor.close()
        return np.unique(shotlist)
    
    def get_entries(self, shot=[], date=[], xp=[]):
        # return list of lobgook entries (dictionaries) for shot(s)
        if shot and not iterable(shot):
            shot = [shot]
        if xp or date:
            shot.extend(self.get_shotlist(date=date, xp=xp))
        if shot:
            self._shot_query(shot=shot)
        entries = []
        for sh in np.unique(shot):
            entries.extend(self.logbook[sh])
        return entries


class Shot(MutableMapping):

    def __init__(self, shot, root=None, parent=None):
        self.shot = shot
        self.xp = self._get_xp  # DRS 9/30/2015
        self.date = self._get_date  # DRS 9/30/2015
        self._root = root
        self._parent = parent
        modules = root._get_modules()
        self._signals = {module: Factory(module, root=root, shot=shot,
                                         parent=self) for module in modules}

    def __getattr__(self, name):
        name_lower = name.lower()
        try:
            return self._signals[name_lower]
        except:
            pass

    def __repr__(self):
        return '<shot# {}>'.format(self.shot)

    def __iter__(self):
        # return iter(self._signals.values())
        return iter(self._signals)

    def __contains__(self, value):
        return value in self._signals

    def __len__(self):
        return len(self._signals.keys())

    def __delitem__(self, item):
        pass

    def __getitem__(self, item):
        return self._signals[item]

    def __setitem__(self, item, value):
        pass

    def __dir__(self):
        return self._signals.keys()
    
    def _get_xp(self):
        # query logbook for XP, return XP
        return None
    
    def _get_date(self):
        # query logbook for rundate, return rundate
        return None
    
    def logbook(self):
        # added 9/30/2015 DRS
        # query logbook for entries, return list of LogbookEntry
        pass


def Factory(module, root=None, shot=None, parent=None):
    try:
        module = module.lower()
        module_path = os.path.join(FDF_DIR, 'modules', module)
        parse_tree = ET.parse(os.path.join(module_path,
                                           ''.join([module, '.xml'])))
        module_tree = parse_tree.getroot()
        DiagnosticClassName = ''.join(['Diagnostic', module.capitalize()])
        if DiagnosticClassName not in Container._classes:
            DiagnosticClass = type(DiagnosticClassName, (Container,), {})
            init_class(DiagnosticClass, module_tree, root=root, diagnostic=module)
            Container._classes[DiagnosticClassName] = DiagnosticClass
        else:
            DiagnosticClass = Container._classes[DiagnosticClassName]

        return DiagnosticClass(module_tree, shot=shot, parent=parent)

    except IOError:
        print("{} not found in modules directory".format(module))
        raise


class Container(object):
    _instances = {}
    _classes = {}

    def __init__(self, module_tree, **kwargs):

        cls = self.__class__

        for read_only in ['parent']:
            setattr(self, '_'+read_only, kwargs.get(read_only, None))

        try:
            self.shot = kwargs['shot']
        except:
            pass

        if self.shot is not None:
            try:
                cls._instances[cls][self.shot].append(self)
            except:
                cls._instances[cls][self.shot] = [self]

        for node in module_tree.findall('node'):
            NodeClassName = ''.join(['Node', cls._name.capitalize()])
            if NodeClassName not in cls._classes:
                NodeClass = type(NodeClassName, (Node, cls), {})
                cls._classes[NodeClassName] = NodeClass
            else:
                NodeClass = cls._classes[NodeClassName]
            setattr(self, node.get('name'), NodeClass(node, parent=self))

        for element in module_tree.findall('axis'):
            signal_list = parse_signal(self, element)
            for signal_dict in signal_list:
                SignalClassName = ''.join(['Signal', cls._name.capitalize()])
                if SignalClassName not in cls._classes:
                    SignalClass = type(SignalClassName, (Signal, cls), {})
                    parse_method(SignalClass, element)
                    cls._classes[SignalClassName] = SignalClass
                else:
                    SignalClass = cls._classes[SignalClassName]
                SignalObj = SignalClass(**signal_dict)
                setattr(self, '_'+signal_dict['name'], SignalObj)

        for branch in module_tree.findall('container'):
            ContainerClassName = ''.join(['Container', branch.get('name').capitalize()])
            if ContainerClassName not in cls._classes:
                ContainerClass = type(ContainerClassName, (cls, Container), {})
                init_class(ContainerClass, branch)
                cls._classes[ContainerClassName] = ContainerClass
            else:
                ContainerClass = cls._classes[ContainerClassName]
            ContainerObj = ContainerClass(branch, parent=self)
            setattr(self, branch.get('name'), ContainerObj)

        for element in module_tree.findall('signal'):
            signal_list = parse_signal(self, element)
            for signal_dict in signal_list:
                SignalClassName = ''.join(['Signal', cls._name.capitalize()])
                if SignalClassName not in cls._classes:
                    SignalClass = type(SignalClassName, (Signal, cls), {})
                    parse_method(SignalClass, element)
                    cls._classes[SignalClassName] = SignalClass
                else:
                    SignalClass = cls._classes[SignalClassName]
                SignalObj = SignalClass(**signal_dict)
                refs = parse_refs(self, element, SignalObj._transpose)
                if not refs:
                    refs = SignalObj.axes
                for axis, ref in zip(SignalObj.axes, refs):
                    setattr(SignalObj, axis, getattr(self, '_'+ref))
                setattr(self, signal_dict['name'], SignalObj)

    def __getattr__(self, attribute):
        if not hasattr(self, '_parent') or self._parent is None:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                                 type(self), attribute))
        attr = getattr(self._parent, attribute)
        if inspect.ismethod(attr):
            return types.MethodType(attr.im_func, self)
        else:
            return attr


def init_class(cls, module_tree, **kwargs):

    cls._name = module_tree.get('name')
    if cls not in cls._instances:
        cls._instances[cls] = {}

    for read_only in ['root', 'diagnostic']:
        try:
             setattr(cls, '_'+read_only, kwargs[read_only])
             print(cls._name, read_only, kwargs.get(read_only, 'Not there'))
        except:
            pass

    for item in ['mdstree', 'mdspath', 'units']:
        getitem = module_tree.get(item)
        if getitem is not None:
            setattr(cls, item, getitem)

    parse_method(cls, module_tree)

def parse_method(obj, module_tree):
    diagnostic = modules.__getattribute__(obj._diagnostic)
    for method in module_tree.findall('method'):
        method_text = method.text
        if method_text is None:
            method_text = method.get('name')
        module_file = diagnostic.__getattribute__(method_text)
        method_from_file = module_file.__getattribute__(method_text)
        setattr(obj, method.get('name'), method_from_file)


def base_container(container):
    parent_container = container
    while type(parent_container._parent) is not Shot:
        parent_container = parent_container._parent
    return parent_container


def parse_signal(obj, element):
    units = parse_units(obj, element)
    axes, transpose = parse_axes(obj, element)
    num = element.get('range')
    if num is None:
        name = element.get('name')
        mdspath, dim_of = parse_mdspath(obj, element)
        mdstree = parse_mdstree(obj, element)
        error = parse_error(obj, element)
        signal_dict = [{'name': name, 'units': units, 'axes': axes,
                        'mdsnode': mdspath, 'mdstree': mdstree,
                        'dim_of': dim_of, 'error': error, 'parent':obj,
                        '_transpose': transpose}]
    else:
        num = int(num)
        signal_dict = []
        digits = int(np.ceil(np.log10(num-1)))
        for index in range(num):
            name = element.get('name').format(str(index).zfill(digits))
            mdspath, dim_of = parse_mdspath(obj, element)
            mdspath = mdspath.format(str(index).zfill(digits))
            mdstree = parse_mdstree(obj, element)
            error = parse_error(obj, element)
            signal_dict.append({'name': name, 'units': units, 'axes': axes,
                        'mdsnode': mdspath, 'mdstree': mdstree,
                        'dim_of': dim_of, 'error': error, 'parent':obj,
                        '_transpose': transpose})
    return signal_dict


def parse_axes(obj, element):
    axes = []
    refs = []
    transpose = None
    time_ind = 0
    try:
        axes = [axis.strip() for axis in element.get('axes').split(',')]
        if 'time' in axes:
            time_ind = axes.index('time')
            if time_ind is not 0:
                transpose = range(len(axes))
                transpose.pop(time_ind)
                transpose.insert(0, time_ind)
                axes.pop(time_ind)
                axes.insert(0, 'time')
    except:
        pass

    return axes, transpose

def parse_refs(obj, element, transpose=None):
    refs = None
    try:
        refs = [ref.strip() for ref in element.get('axes_refs').split(',')]
        if transpose is not None:
            refs = [refs[index] for index in transpose]
    except:
        pass

    return refs

def parse_units(obj, element):
    units = element.get('units')
    if units is None:
        try:
            units = obj.units
        except:
            pass
    return units


def parse_error(obj, element):
    error = element.get('error')
    if error is not None:
        mdspath = element.get('mdspath')
        if mdspath is None:
            try:
                mdspath = obj.mdspath
                error = '.'.join([mdspath, error])
            except:
                pass
        else:
            error = '.'.join([mdspath, error])
    return error


def parse_mdspath(obj, element):
    mdspath = element.get('mdspath')
    try:
        dim_of = int(element.get('dim_of'))
    except:
        dim_of = None
    if mdspath is None:
        try:
            mdspath = obj.mdspath
        except:
            pass
    if mdspath is not None:
        mdspath = '.'.join([mdspath, element.get('mdsnode')])
    else:
        mdspath = element.get('mdsnode')
    return mdspath, dim_of


def parse_mdstree(obj, element):
    mdstree = element.get('mdstree')
    if mdstree is None:
        mdstree = obj.mdstree
    return mdstree


def iterable(obj):
    try:
        iter(obj)
        if type(obj) is str:
            return False
        return True
    except TypeError:
        return False


class Node(object):
    def __init__(self, element, parent=None):
        self._parent = parent
        self._name = element.get('name')
        self.mdspath = parse_mdspath(self, element)

if __name__ == '__main__':
    nstx = Machine('nstx')
    nstx.addshot(140000)
    nstx.logbook(140000)
    sl = nstx.get_shotlist(xp=1048, verbose=True)
    nstx.addshot(xp=1048)
    

