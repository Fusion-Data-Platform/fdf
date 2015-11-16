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
import sys, os, importlib
import fdf_globals
from fdf_signal import Signal
import numpy as np
import datetime as dt
#import modules   # I think this import is unused - DRS 10/17/15
from collections import MutableMapping, Mapping
import MDSplus as mds
import types
import inspect
import pymssql
import matplotlib.pyplot as plt


FDF_DIR = fdf_globals.FDF_DIR
MDS_SERVERS = fdf_globals.MDS_SERVERS
EVENT_SERVERS = fdf_globals.EVENT_SERVERS
LOGBOOK_CREDENTIALS = fdf_globals.LOGBOOK_CREDENTIALS
FdfError = fdf_globals.FdfError
machineAlias = fdf_globals.machineAlias


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
    _connections = []
    _parent = None
    _modules = None

    def __init__(self, name='nstx', shotlist=[], xp=[], date=[]):
        self._shots = {}  # shot dictionary with shot number (int) keys
        self._classlist = {} # unused as of 10/14/2015, DRS
        self._name = machineAlias(name)
        self._logbook = Logbook(name=self._name, root=self)
        self.s0 = Shot(0, root=self, parent=self)
        self._eventConnection = mds.Connection(EVENT_SERVERS[self._name])

        if len(self._connections) is 0:
            print('Precaching MDS server connections...')
            for _ in range(2):
                try:
                    connection = mds.Connection(MDS_SERVERS[self._name])
                    connection.tree = None
                    self._connections.append(connection)
                except:
                    msg = 'MDSplus connection to {} failed'.format(
                        MDS_SERVERS[self._name])
                    raise FdfError(msg)
            print('Finished.')

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
            raise AttributeError("'{}' object has no attribute '{}'".format(
                             type(self), name))

    def __repr__(self):
        return '<machine {}>'.format(self._name.upper())

    def __iter__(self):
        return iter(self._shots.values())

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
        return d

    def _get_connection(self, shot, tree):
        for connection in self._connections:
            if connection.tree == (tree, shot):
                self._connections.remove(connection)
                self._connections.insert(0, connection)
                return connection
        connection = self._connections.pop()
        try:
            connection.closeAllTrees()
        except:
            pass
        try:
            connection.openTree(tree, shot)
            connection.tree = (tree, shot)
        except:
            connection.tree = (None, None)
        finally:
            self._connections.insert(0, connection)
        return connection

    def _get_mdsdata(self, signal):
        # shot = base_container(signal)._parent.shot
        shot = signal.shot
        if shot is 0:
            print('No MDS data exists for model tree')
            return None
        connection = self._get_connection(shot, signal._mdstree)
        try:
            data = connection.get(signal._mdsnode)
        except:
            msg = "MDSplus connection error for tree '{}' and node '{}'".format(
                signal._mdstree, signal._mdsnode)
            raise FdfError(msg)
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
        try:
            data = signal._postprocess(data)
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
        if date:
            shots.extend(self._logbook.get_shotlist(date=date,
                                                    verbose=verbose))
        
        for shot in np.unique(shots):
            if shot not in self._shots:
                self._shots[shot] = Shot(shot, root=self, parent=self)

    def addxp(self, xp=[], verbose=False):
        """
        Add all shots for one or more XPx
        
        **Usage**

            >>> nstx.addxp(1032)
            >>> nstx.addxp(xp=1013)
            >>> nstx.addxp([1042, 1016])
        
        """
        self.addshot(xp=xp, verbose=verbose)

    def adddate(self, date=[], verbose=False):
        """
        Add all shots for one or more dates (format YYYYMMDD)
        
        **Usage**

            >>> nstx.adddate(date=20100817)
        
        """
        self.addshot(date=date, verbose=verbose)

    def list_shots(self):
        for shotnum in self._shots:
            shotObj = self._shots[shotnum]
            print('{} in XP {} on {}'.format(
                shotObj.shot, shotObj.xp, shotObj.date))

    def get_shotlist(self, date=[], xp=[], verbose=False):
        """
        Get a list of shots
        
        **Usage**

            >>> shots = nstx.get_shotlist(xp=1013)
        
        """
        return self._logbook.get_shotlist(date=date, xp=xp, verbose=verbose)

    def filter_shots(self, date=[], xp=[]):
        """
        Get a Machine-like object with an immutable shotlist for XP(s) 
        or date(s)
        """
        self.addshot(xp=xp, date=date)
        return ImmutableMachine(xp=xp, date=date, parent=self)
        
    def setevent(self, event, shot_number=None, data=None):
        event_data = bytearray()
        if shot_number is not None:
            shot_data = shot_number // 256**np.arange(4) % 256
            event_data.extend(shot_data.astype(np.ubyte))
        if data is not None:
            event_data.extend(str(data))
        mdsdata = mds.mdsdata.makeData(np.array(event_data))
        event_string = 'setevent("{}", {})'.format(event, mdsdata)
        status = self._eventConnection.get(event_string)
        return status

    def wfevent(self, event, timeout=0):
        event_string = 'kind(_data=wfevent("{}",*,{})) == 0BU ? "timeout"' \
                       ': _data'.format(event, timeout)
        data = self._eventConnection.get(event_string).value
        if type(data) is str:
            raise FdfError('Timeout after {}s in wfevent'.format(timeout))
        if not data.size:
            return None
        if data.size > 3:
            shot_data = data[0:4]
            shot_number = np.sum(shot_data * 256**np.arange(4))
            data = data[4:]
            return shot_number, ''.join(map(chr, data))
        return data

    def logbook(self):
        """
        Print logbook entries for all shots
        """
        for shotnum in self._shots:
            shotObj = self._shots[shotnum]
            shotObj.logbook()


class ImmutableMachine(Mapping):
    
    def __init__(self, xp=[], date=[], parent=None):
        self._shots = {}
        self._parent = parent
        shotlist = self._parent.get_shotlist(xp=xp, date=date)
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
        return '<immutable machine {}>'.format(self._name.upper())

    def __iter__(self):
        return iter(self._shots.values())

    def __contains__(self, value):
        return value in self._shots

    def __len__(self):
        return len(self._shots.keys())

    def __getitem__(self, item):
        pass

    def __dir__(self):
        return ['s{}'.format(shot) for shot in self._shots]

    def logbook(self):
        for shotnum in self._shots:
            shotObj = self._shots[shotnum]
            shotObj.logbook()
            
    def list_shots(self):
        for shotnum in self._shots:
            shotObj = self._shots[shotnum]
            print('{} in XP {} on {}'.format(
                shotObj.shot, shotObj.xp, shotObj.date))


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
        self._modules = {module: None for module in root._get_modules()}
        self.xp = self._get_xp()
        self.date = self._get_date()
        self._efits = []

    def __getattr__(self, attribute):
        # first see if the attribute is in the Machine object
        try:
            attr = getattr(self._parent, attribute)
            if inspect.ismethod(attr):
                return types.MethodType(attr.im_func, self)
            else:
                return attr
        except:
            pass  # failed, so check other locations
        if attribute in self._modules:
            if self._modules[attribute] is None:
                self._modules[attribute] = Factory(attribute, root=self._root,
                                                   shot=self.shot, parent=self)
            return self._modules[attribute]
        raise AttributeError("Shot object has no attribute '{}'".format(attribute))

    def __repr__(self):
        return '<Shot {}>'.format(self.shot)

    def __iter__(self):
        # return iter(self._modules.values())
        return iter(self._modules)

    def __contains__(self, value):
        return value in self._modules

    def __len__(self):
        return len(self._modules.keys())

    def __delitem__(self, item):
        pass

    def __getitem__(self, item):
        return self._modules[item]

    def __setitem__(self, item, value):
        pass

    def __dir__(self):
        return self._modules.keys()

    def _get_xp(self):
        # query logbook for XP, return XP (list if needed)
        if self._logbook and not self._logbook_entries:
            self._logbook_entries = self._logbook.get_entries(shot=self.shot)
        
        xplist = []
        for entry in self._logbook_entries:
            xplist.append(entry['xp'])
        return np.unique(xplist)

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

    def plot(self, overwrite=False, label=None, multi=False):

        if not overwrite and not multi:
            plt.figure()
            plt.subplot(1, 1, 1)
        if self.shape != self.time.shape:
            msg = 'Dimension mismatch: {}\n  shape data {} shape time ()'.format(
                self._name, self.shape, self.time.shape)
            raise FdfError(msg)
        if self.size==0 or self.time.size==0:
            msg = 'Empty data and/or time axis: {}\n  shape data {} shape time {}'.format(
                self._name, self.shape, self.time.shape)
            raise FdfError(msg)
        plt.plot(self.time[:], self[:], label=label)
        title = self._title if self._title else self._name
        if not overwrite or multi:
            plt.suptitle('Shot #{}'.format(self.shot), x=0.5, y=1.00,
                         fontsize=12, horizontalalignment='center')
            plt.ylabel('{} ({})'.format(self._name.upper(), self.units))
            plt.title('{} {}'.format(self._container.upper(), title),
                      fontsize=12)
            plt.xlabel('{} ({})'.format(self.time._name.capitalize(),
                                        self.time.units))
        plt.legend()
        plt.show()

    def check_efit(self):
        if len(self._efits):
            return self._efits
        trees = ['efit{}'.format(str(index).zfill(2)) for index in range(1, 7)]
        trees.extend(['lrdfit{}'.format(str(index).zfill(2))
                      for index in range(1, 13)])
        tree_exists = []
        for tree in trees:
            data = None
            connection = self._get_connection(self.shot, tree)
            try:
                data = connection.get('\{}::userid'.format(tree)).value
            except:
                pass
            if data and data is not '*':
                tree_exists.append(tree)
        self._efits = tree_exists
        return self._efits


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
            raise FdfError('Cursor error')
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
                    year = rundate[0:4]
                    month = rundate[4:6]
                    day = rundate[6:8]
                    row['rundate'] = dt.date(int(year), int(month), int(day))
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
            year = rundate[0:4]
            month = rundate[4:6]
            day = rundate[6:8]
            row['rundate'] = dt.date(int(year), int(month), int(day))
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


def Factory(module_branch, root=None, shot=None, parent=None):
    global _tree_dict

    """
    Factory method
    """

    try:
        module_branch = module_branch.lower()
        module_list = module_branch.split('.')
        module = module_list[-1]
        branch_str = ''.join([word.capitalize() for word in module_list])
        if module_branch not in _tree_dict:
            module_path = os.path.join(FDF_DIR, 'modules', *module_list)
            parse_tree = ET.parse(os.path.join(module_path,
                                               ''.join([module, '.xml'])))
            module_tree = parse_tree.getroot()
            _tree_dict[module_branch] = module_tree
        ContainerClassName = ''.join(['Container', branch_str])
        if ContainerClassName not in Container._classes:
            ContainerClass = type(ContainerClassName, (Container,), {})
            init_class(ContainerClass, _tree_dict[module_branch], root=root,
                       container=module, classparent=parent.__class__)
            Container._classes[ContainerClassName] = ContainerClass
        else:
            ContainerClass = Container._classes[ContainerClassName]

        return ContainerClass(_tree_dict[module_branch], shot=shot,
                              parent=parent, top=True)

    except None:
        print("{} not found in modules directory".format(module))
        raise


class Container(object):
    """
    Container class
    """
    _instances = {}
    _classes = {}

    def __init__(self, module_tree, top=False, **kwargs):

        cls = self.__class__

        self._signals = {}
        self._containers = {}
        self._subcontainers = {}

        self._title = module_tree.get('title')
        self._desc = module_tree.get('desc')

        for read_only in ['parent']:
            setattr(self, '_'+read_only, kwargs.get(read_only, None))

        try:
            self.shot = kwargs['shot']
            self._mdstree = kwargs['mdstree']
        except:
            pass

        if self.shot is not None:
            try:
                cls._instances[cls][self.shot].append(self)
            except:
                cls._instances[cls][self.shot] = [self]

        if top:
            self._get_subcontainers()

        for node in module_tree.findall('node'):
            NodeClassName = ''.join(['Node', cls._name.capitalize()])
            if NodeClassName not in cls._classes:
                NodeClass = type(NodeClassName, (Node, cls), {})
                cls._classes[NodeClassName] = NodeClass
            else:
                NodeClass = cls._classes[NodeClassName]
            NodeClass._mdstree = parse_mdstree(self, node)
            setattr(self, node.get('name'), NodeClass(node, parent=self))

        for element in module_tree.findall('axis'):
            signal_list = parse_signal(self, element)
            branch_str = self._get_branchstr()
            for signal_dict in signal_list:
                SignalClassName = ''.join(['Axis', branch_str])
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
                setattr(self, ''.join(['_', signal_dict['_name']]), SignalObj)

        for branch in module_tree.findall('container'):
            name = branch.get('name')
            branch_str = self._get_branchstr()
            ContainerClassName = ''.join(['Container', branch_str,
                                          name.capitalize()])
            if ContainerClassName not in cls._classes:
                ContainerClass = type(ContainerClassName, (cls, Container), {})
                init_class(ContainerClass, branch, classparent=cls)
                cls._classes[ContainerClassName] = ContainerClass
            else:
                ContainerClass = cls._classes[ContainerClassName]
            ContainerObj = ContainerClass(branch, parent=self)
            setattr(self, name, ContainerObj)
            self._containers[name] = ContainerObj

        for element in module_tree.findall('signal'):
            signal_list = parse_signal(self, element)
            branch_str = self._get_branchstr()
            for signal_dict in signal_list:
                # name = element.get('name').format('').capitalize()
                SignalClassName = ''.join(['Signal', branch_str])
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
                self._signals[signal_dict['_name']] = SignalObj

        if top and hasattr(self, '_preprocess'):
            self._preprocess()

    def __getattr__(self, attribute):

        try:
            if self._subcontainers[attribute] is None:
                branch_path = '.'.join([self._get_branch(), attribute])
                self._subcontainers[attribute] = \
                    Factory(branch_path, root=self._root,
                            shot=self.shot, parent=self)

            return self._subcontainers[attribute]
        except KeyError:
            pass

        if not hasattr(self, '_parent') or self._parent is None:
            raise AttributeError("Attribute '{}' not found".format(attribute))

        if hasattr(self._parent, '_signals') and \
                attribute in self._parent._signals:
            raise AttributeError("Attribute '{}' not found".format(attribute))
        attr = getattr(self._parent, attribute)
        if Container in attr.__class__.mro() and attribute[0] is not '_':
            raise AttributeError("Attribute '{}' not found".format(attribute))
        if inspect.ismethod(attr):
            return types.MethodType(attr.im_func, self)
        else:
            return attr

    def _get_subcontainers(self):
        if len(self._subcontainers) is 0:
            container_dir = self._get_path()
            if not os.path.isdir(container_dir):
                return
            files = os.listdir(container_dir)
            self._subcontainers = {container: None for container in
                                  files if os.path.isdir(
                                  os.path.join(container_dir, container)) and
                                  container[0] is not '_'}

    @classmethod
    def _get_path(cls):
        branch = cls._get_branch().split('.')
        path = os.path.join(FDF_DIR, 'modules')
        for step in branch:
            newpath = os.path.join(path, step)
            if not os.path.isdir(newpath):
                break
            path = newpath
        return path

    def __dir__(self):
#        print('in dir')
        items = self.__dict__.keys()
        items.extend(self.__class__.__dict__.keys())
        if Signal not in self.__class__.mro():
            items.extend(self._subcontainers.keys())
        return [item for item in set(items).difference(self._base_items)
                if item[0] is not '_']

    def __iter__(self):
        if not len(self._signals):
            items = self._containers.values()
            # items.extend(self._subcontainers.values())
        else:
            items = self._signals.values()
        return iter(items)

    @classmethod
    def _get_branch(cls):
        branch = cls._name
        parent = cls._classparent
        while parent is not Shot and parent.__class__ is not Shot:
            branch = '.'.join([parent._name, branch])
            parent = parent._classparent
        return branch

    @classmethod
    def _get_branchstr(cls):
        branch = cls._get_branch()
        return ''.join([sub.capitalize() for sub in branch.split('.')])


def init_class(cls, module_tree, **kwargs):

    cls._name = module_tree.get('name')
    if cls not in cls._instances:
        cls._instances[cls] = {}

    for read_only in ['root', 'container', 'classparent']:
        try:
            setattr(cls, '_'+read_only, kwargs[read_only])
            # print(cls._name, read_only, kwargs.get(read_only, 'Not there'))
        except:
            pass

    for item in ['mdstree', 'mdspath', 'units']:
        getitem = module_tree.get(item)
        if getitem is not None:
            setattr(cls, '_'+item, getitem)

    cls._base_items = set(cls.__dict__.keys())
    parse_method(cls, module_tree)


def parse_method(obj, module_tree):
    objpath = obj._get_path()
    sys.path.insert(0, objpath)
    for method in module_tree.findall('method'):
        method_text = method.text
        if method_text is None:
            method_text = method.get('name')
        module_object = importlib.import_module(method_text)
        method_from_object = module_object.__getattribute__(method_text)
        setattr(obj, method.get('name'), method_from_object)
    sys.path.pop(0)


def base_container(container):
    parent_container = container
    while type(parent_container._parent) is not Shot:
        parent_container = parent_container._parent
    return parent_container


def parse_signal(obj, element):
    units = parse_units(obj, element)
    axes, transpose = parse_axes(obj, element)
    number_range = element.get('range')
    if number_range is None:
        name = element.get('name')
        title = element.get('title')
        desc = element.get('desc')
        mdspath, dim_of = parse_mdspath(obj, element)
        mdstree = parse_mdstree(obj, element)
        error = parse_error(obj, element)
        signal_dict = [{'_name': name, 'units': units, 'axes': axes,
                        '_mdsnode': mdspath, '_mdstree': mdstree,
                        '_dim_of': dim_of, '_error': error, '_parent': obj,
                        '_transpose': transpose, '_title': title,
                        '_desc': desc}]
    else:
        number_list = number_range.split(',')
        len_number_list = len(number_list)
        if len_number_list == 1:
            start = 0
            end = int(number_list[0])
        else:
            start = int(number_list[0])
            end = int(number_list[1])+1
        signal_dict = []
        if len_number_list == 3:
            # 3rd item, if present, controls zero padding (cf. BES and magnetics)
            digits = int(number_list[2])
        else:
            digits = int(np.ceil(np.log10(end-1)))
        for index in range(start, end):
            name = element.get('name').format(str(index).zfill(digits))
            title = None
            if element.get('title'):
                title = element.get('title').format(str(index).zfill(digits))
            desc = None
            if element.get('desc'):
                desc = element.get('desc').format(str(index).zfill(digits))
            mdspath, dim_of = parse_mdspath(obj, element)
            mdspath = mdspath.format(str(index).zfill(digits))
            mdstree = parse_mdstree(obj, element)
            error = parse_error(obj, element)
            signal_dict.append({'_name': name, 'units': units, 'axes': axes,
                                '_mdsnode': mdspath, '_mdstree': mdstree,
                                '_dim_of': dim_of, '_error': error,
                                '_parent': obj, '_transpose': transpose,
                                '_title': title, '_desc': desc})
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
                mdspath = obj._mdspath
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
                mdspath = obj._mdspath
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
    if mdstree is None and hasattr(obj, '_mdstree'):
        mdstree = obj._mdstree
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
        self._mdsnode = parse_mdspath(self, element)
        self._data = None
        self._title = element.get('title')
        self._desc = element.get('desc')
        self.units = element.get('units')

    def __repr__(self):
        if self._data is None:
            self._data = self._get_mdsdata()
        return str(self._data)

    def __getattr__(self, attribute):
        if attribute is '_parent':
            raise AttributeError("'{}' object has no attribute '{}'".format(
                                 type(self), attribute))
        if self._parent is None:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                                 type(self), attribute))
        attr = getattr(self._parent, attribute)
        if inspect.ismethod(attr):
            return types.MethodType(attr.im_func, self)
        else:
            return attr

if __name__ == '__main__':
    nstx = Machine()
    xp = nstx.filter_shots(xp=1037)
