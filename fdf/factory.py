# -*- coding: utf-8 -*-
"""
Root module for the FDF package.

**Classes**

* Machine - root class for the FDF package
* Shot - shot container class
* Logbook - logbook connection class
* Container - diagnostic container class
* Node - mdsplus signal node class

"""

"""
Created on Thu Jun 18 10:38:40 2015
@author: ktritz
"""

import xml.etree.ElementTree as ET
import os
import fdf_globals
from fdf_signal import Signal
import numpy as np
import datetime as dt
import modules
from collections import MutableMapping, OrderedDict
import MDSplus as mds
import types
import inspect
import pymssql


FDF_DIR = fdf_globals.FDF_DIR
MDS_SERVERS = fdf_globals.MDS_SERVERS
LOGBOOK_CREDENTIALS = fdf_globals.LOGBOOK_CREDENTIALS
FdfError = fdf_globals.FdfError


class Machine(MutableMapping):
    """
    Factory root class that contains shot objects and MDS access methods.
    
    Note that fdf.factory.Machine is exposed in fdf.__init__, so fdf.Machine
    is valid.

    **Usage**::

        >>> import fdf
        >>> nstx = fdf.Machine('nstx')
        >>> nstx.s140000.logbook()
        >>> nstx.addshots(xp=1048)
        >>> nstx.s140000.mpts.plot()
        >>> nstx.listshot()

    Machine class contains a model shot object: nstx.s0

    Shot data can be accessed directly through the Machine class::

        >>> nstx.s141398
        >>> nstx.s141399

    Alternatively, a list of shot #'s may be provided during initialization::

        >>> nstx = Machine(name='nstx', shotlist=[141398, 141399])

    Or added later using the method addshot()::

        >>> nstx.addshot([141398, 141399])

    """

    # Maintain a dictionary of cached MDS server connections to speed up
    # access for multiple shots and trees. This is a static class variable
    # to avoid proliferation of MDS server connections
    _connections = OrderedDict()
    _parent = None
    _modules = None

    def __init__(self, name='nstx', shotlist=[], xp=[], date=[]):
        self._shots = {}  # shot dictionary with shot number (int) keys
        self._xps = {} # XP dictionary
        self._classlist = {}
        self._name = name.lower()

        if self._name not in LOGBOOK_CREDENTIALS or \
                self._name not in MDS_SERVERS:
            txt = '\n{} is not a valid machine.\n'.format(self._name.upper())
            txt = txt + 'Valid machines are:\n'
            for machine in LOGBOOK_CREDENTIALS:
                txt = txt + '  {}\n'.format(machine.upper())
            raise FdfError(txt)

        self._logbook = Logbook(name=self._name, root=self)
        self.s0 = Shot(0, root=self, parent=self)

        if len(self._connections) is 0:
            print('Precaching MDS server connections...')
            for _ in range(2):
                try:
                    self._connections[mds.Connection(MDS_SERVERS[self._name])] = None
                except:
                    txt = 'MDSplus connection to {} failed.'.format(MDS_SERVERS[self._name])
                    raise FdfError(txt)
            print('Finished.')

        # add shots
        if shotlist or xp or date:
            self.addshot(shotlist=shotlist, xp=xp, date=date)

    def __getattr__(self, name):
        # used for attribute referencing: s = nstx.s140000
        try:
            shot = int(name.split('s')[1])
            if (shot not in self._shots):
                self._shots[shot] = Shot(shot, root=self, parent=self)
            return self._shots[shot]
        except:
            try:
                xp = int(name.split('xp')[1])
                if (xp not in self._xps):
                    self.addxp(xp)
                return self._xps[xp]
            except:
                raise AttributeError("'{}' object has no attribute '{}'".format(
                                 type(self), name))

    def __repr__(self):
        return '<machine {}>'.format(self._name.upper())

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
        # used for dictionary referencing:  s = nstx[140000]
        # note that getitem fails to catch missing key, 
        # but getattr does catch missing key
        if item == 0:
            return self.s0
        return self._shots[item]

    def __setitem__(self, item, value):
        pass

    def __dir__(self):
        d = ['s0']
        d.extend(['s{}'.format(shot) for shot in self._shots])
        d.extend(['xp{}'.format(xp) for xp in self._xps])
        return d

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
        connection = self._get_connection(shot, signal._mdstree)
        data = connection.get(signal._mdsnode)
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

        if self._modules is None:
            module_dir = os.path.join(FDF_DIR, 'modules')
            self._modules = [module for module in os.listdir(module_dir)
                        if os.path.isdir(os.path.join(module_dir, module)) and
                        module[0] is not '_']
        return self._modules

    def addshot(self, shotlist=[], date=[], xp=[], verbose=False):
        """
        Load shots into the Machine class

        **Usage**

            >>> nstx.addshot([140000 140001])
            >>> nstx.addshot(xp=1032)
            >>> nstx.addshot(date=20100817, verbose=True)

        Note: You can reference shots even if the shots have not been loaded.

        """
        if not iterable(shotlist):
            shotlist = [shotlist]
        if not iterable(xp):
            xp = [xp]
        if not iterable(date):
            date = [date]
        
        shots = []
        if shotlist:
            shots.extend([shotlist])
        if xp:
            shots.extend(self._logbook.get_shotlist(xp=xp,
                                                    verbose=verbose))
            for xpp in xp:
                self._xps[xpp] = XP(xpp, root=self, parent=self)
        if date:
            shots.extend(self._logbook.get_shotlist(date=date,
                                                    verbose=verbose))
        
        for shot in np.unique(shots):
            if shot not in self._shots:
                self._shots[shot] = Shot(shot, root=self, parent=self)

    def addxp(self, xp=[], verbose=False):
        self.addshot(xp=xp, verbose=verbose)

    def adddate(self, date=[], verbose=False):
        self.addshot(date=date, verbose=verbose)

    def listshot(self):
        for key in np.sort(self._shots.keys()):
            shot = self._shots[key]
            print('{} in XP {} on {}'.format(shot.shot, shot.xp, shot.date))

    def get_shotlist(self, date=[], xp=[], verbose=False):
        # return a list of shots
        return self._logbook.get_shotlist(date=date, xp=xp, verbose=verbose)


class XP(Machine):
    
    def __init__(self, xp, root=None, parent=None):
        self.xp = xp
        self._root = root
        self._parent = parent
        self._shots = {}
        self._logbook = self._parent._logbook
        self._logbook_entries = {}
        
        shotlist = self._parent.get_shotlist(xp=self.xp)
        for shot in shotlist:
            self._shots[shot] = getattr(self._parent, 's{}'.format(shot))

    def __getattr__(self, name):
        try:
            shot = int(name.split('s')[1])
            return self._shots[shot]
        except:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                type(self), name))

    def __repr__(self):
        return '<XP {}>'.format(self.xp)

    def __dir__(self):
        return ['s{}'.format(shot) for shot in self._shots]

    def logbook(self):
        # print a list of logbook entries
        print('Logbook entries for XP {}'.format(self.xp))
        if not self._logbook_entries:
            self._logbook_entries = self._logbook.get_entries(xp=self.xp)
        for entry in self._logbook_entries:
            print('************************************')
            print(('{shot} on {rundate} in XP {xp}\n'
                   '{username} in topic {topic}\n\n'
                   '{text}').format(**entry))
        print('************************************')

    def addshot(*args, **kwargs):
        pass
    
    def get_shotlist(*args, **kwargs):
        pass


class Shot(MutableMapping):

    def __init__(self, shot, root=None, parent=None):
        self.shot = shot
        self._shotobj = self
        self._root = root
        self._parent = parent
        try:
            self._logbook = self._root._logbook
        except:
            txt = 'No logbook connection for shot {}'.format(self.shot)
            raise FdfError(txt)
        self._logbook_entries = []
        modules = root._get_modules()
        self._signals = {module: Factory(module, root=root, shot=shot,
                                         parent=self) for module in modules}
        self.xp = self._get_xp()
        self.date = self._get_date()

    def __getattr__(self, name):
        name_lower = name.lower()
        try:
            return self._signals[name_lower]
        except:
            pass

    def __repr__(self):
        return '<Shot {}>'.format(self.shot)

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
        # added xp and date to dir(shot), DRS, 10/13/15
        d = self._signals.keys()
        d.extend(['xp', 'date'])
        return d

    def _get_xp(self):
        # query logbook for XP, return XP (list if needed)
        if self._logbook and not self._logbook_entries:
            self._logbook_entries = self._logbook.get_entries(shot=self.shot)
        
        xplist = []
        for entry in self._logbook_entries:
            xplist.append(entry['xp'])
        
        if len(np.unique(xplist)) == 1:
            xp = xplist.pop(0)
        elif len(np.unique(xplist)) > 1:
            xp = np.unique(xplist)
        else:
            xp = 0
        return xp

    def _get_date(self):
        # query logbook for rundate, return rundate
        if self._logbook and not self._logbook_entries:
            self._logbook_entries = self._logbook.get_entries(shot=self.shot)
        date = 0
        if self._logbook_entries:
            date = self._logbook_entries[0]['rundate']
        return date

    def logbook(self):
        # print a list of logbook entries
        print('Logbook entries for {}'.format(self.shot))
        if not self._logbook_entries:
            self._logbook_entries = self._logbook.get_entries(shot=self.shot)
        for entry in self._logbook_entries:
            print('************************************')
            print(('{shot} on {rundate} in XP {xp}\n'
                   '{username} in topic {topic}\n\n'
                   '{text}').format(**entry))
        print('************************************')


class Logbook(object):

    def __init__(self, name='nstx', root=None):
        self._name = name.lower()
        self._root = root

        self._credentials = {}
        self._table = ''
        self._shotlist_query_prefix = ''
        self._shot_query_prefix = ''

        self._logbook_connection = None
        self._make_logbook_connection()

        # dict of cached logbook entries
        # kw is shot, value is list of logbook entries
        self.logbook = {}

    def _make_logbook_connection(self):
        self._credentials = LOGBOOK_CREDENTIALS[self._name]
        self._table = self._credentials['table']

        self._shotlist_query_prefix = (
            'SELECT DISTINCT rundate, shot, xp, voided '
            'FROM {} WHERE voided IS null').format(self._table)
        self._shot_query_prefix = (
            'SELECT dbkey, username, rundate, shot, xp, topic, text, entered, voided '
            'FROM {} WHERE voided IS null').format(self._table)

        try:
            self._logbook_connection = pymssql.connect(
                server=self._credentials['server'],
                user=self._credentials['username'],
                password=self._credentials['password'],
                database=self._credentials['database'],
                port=self._credentials['port'],
                as_dict=True)
        except:
            print('Attempting logbook server connection as drsmith')
            try:
                self._logbook_connection = pymssql.connect(
                    server=self._credentials['server'],
                    user='drsmith',
                    password=self._credentials['password'],
                    database=self._credentials['database'],
                    port=self._credentials['port'],
                    as_dict=True)
            except:
                txt = '{} logbook connection failed. '.format(self._name.upper())
                txt = txt + 'Server credentials:'
                for key in self._credentials:
                    txt = txt + '  {0}:{1}'.format(key, self._credentials[key])
                raise FdfError(txt)

    def _get_cursor(self):
        try:
            cursor = self._logbook_connection.cursor()
            cursor.execute('SET ROWCOUNT 500')
        except:
            raise FdfError('Cursor error.')
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
                rows = cursor.fetchall()  # list of logbook entries
                for row in rows:
                    rundate = repr(row['rundate'])
                    yr=rundate[0:4]; mon=rundate[4:6]; day = rundate[6:8]
                    row['rundate'] = dt.date(int(yr), int(mon), int(day))
                self.logbook[sh] = rows

    def get_shotlist(self, date=[], xp=[], verbose=False):
        # return list of shots for date and/or XP
        cursor = self._get_cursor()
        rows = []
        shotlist = []   # start with empty shotlist

        date_list = date
        if not iterable(date_list):      # if it's just a single date
            date_list = [date_list]   # put it into a list
        for date in date_list:
            query = ('{0} and rundate={1} ORDER BY shot ASC'.
                     format(self._shotlist_query_prefix, date))
            cursor.execute(query)
            rows.extend(cursor.fetchall())
            
        xp_list = xp
        if not iterable(xp_list):           # if it's just a single xp
            xp_list = [xp_list]             # put it into a list
        for xp in xp_list:
            query = ('{0} and xp={1} ORDER BY shot ASC'.
                     format(self._shotlist_query_prefix, xp))
            cursor.execute(query)
            rows.extend(cursor.fetchall())
            
        for row in rows:
            rundate = repr(row['rundate'])
            yr=rundate[0:4]; mon=rundate[4:6]; day = rundate[6:8]
            row['rundate'] = dt.date(int(yr), int(mon), int(day))
        if verbose:
            print('date {}'.format(rows[0]['rundate']))
            for row in rows:
                print('   {shot} in XP {xp}'.format(**row))
        # add shots to shotlist
        shotlist.extend([row['shot'] for row in rows
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
            if sh in self.logbook:
                entries.extend(self.logbook[sh])
        return entries


_tree_dict = {}


def Factory(module, root=None, shot=None, parent=None):
    global _tree_dict

    """
    Factory method
    """

    try:
        module = module.lower()
        if module not in _tree_dict:
            module_path = os.path.join(FDF_DIR, 'modules', module)
            parse_tree = ET.parse(os.path.join(module_path,
                                               ''.join([module, '.xml'])))
            module_tree = parse_tree.getroot()
            _tree_dict[module] = module_tree
        DiagnosticClassName = ''.join(['Diagnostic', module.capitalize()])
        if DiagnosticClassName not in Container._classes:
            DiagnosticClass = type(DiagnosticClassName, (Container,), {})
            init_class(DiagnosticClass, _tree_dict[module], root=root, diagnostic=module)
            Container._classes[DiagnosticClassName] = DiagnosticClass
        else:
            DiagnosticClass = Container._classes[DiagnosticClassName]

        return DiagnosticClass(_tree_dict[module], shot=shot, parent=parent)

    except IOError:
        print("{} not found in modules directory".format(module))
        raise


class Container(object):
    """
    Container class
    """
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
                setattr(self, ''.join(['_',signal_dict['_name']]), SignalObj)

        for branch in module_tree.findall('container'):
            name = branch.get('name')
            ContainerClassName = ''.join(['Container', name.capitalize()])
            if ContainerClassName not in cls._classes:
                ContainerClass = type(ContainerClassName, (cls, Container), {})
                init_class(ContainerClass, branch)
                cls._classes[ContainerClassName] = ContainerClass
            else:
                ContainerClass = cls._classes[ContainerClassName]
            ContainerObj = ContainerClass(branch, parent=self)
            setattr(self, name, ContainerObj)

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
                setattr(self, signal_dict['_name'], SignalObj)

    def __getattr__(self, attribute):
        if not hasattr(self, '_parent') or self._parent is None:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                                 type(self), attribute))
        attr = getattr(self._parent, attribute)
        if inspect.ismethod(attr):
            return types.MethodType(attr.im_func, self)
        else:
            return attr

    def __dir__(self):
        items = self.__dict__.keys()
        items.extend(self.__class__.__dict__.keys())
        return [item for item in set(items).difference(self._base_items)
                if item[0] is not '_']


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

    cls._base_items = set(cls.__dict__.keys())
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
        signal_dict = [{'_name': name, 'units': units, 'axes': axes,
                        '_mdsnode': mdspath, '_mdstree': mdstree,
                        '_dim_of': dim_of, '_error': error, '_parent': obj,
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
            signal_dict.append({'_name': name, 'units': units, 'axes': axes,
                                '_mdsnode': mdspath, '_mdstree': mdstree,
                                '_dim_of': dim_of, '_error': error,
                                '_parent': obj, '_transpose': transpose})
    return signal_dict


def parse_axes(obj, element):
    axes = []
    transpose = None
    time_ind = 0
    try:
        axes = [axis.strip() for axis in element.get('axes').split(',')]
        if 'time' in axes:
            time_ind = axes.index('time')
            if time_ind is not 0:
                transpose = list(range(len(axes)))
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


_path_dict = {}


def parse_mdspath(obj, element):
    global _path_dict

    key = (type(obj), element)
    try:
        return _path_dict[key]
    except KeyError:
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
        _path_dict[key] = (mdspath, dim_of)
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
    """
    Node class
    """
    def __init__(self, element, parent=None):
        self._parent = parent
        self._name = element.get('name')
        self.mdspath = parse_mdspath(self, element)


if __name__ == '__main__':
    nstx = Machine('nstx')
    nstx.get_shotlist(xp=1013, verbose=True)
    nstx.addxp(1013)
    nstx.listshot()


