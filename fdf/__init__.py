"""
A data access/management framework for magnetic fusion experiments.

**Modules**

* ``factory`` - root module for FDF package
* ``fdf_globals`` - package-wide constants
* ``fdf_signal`` - signal class module
* ``fdf/modules/`` - diagnostic sub-modules.

**Usage**

    >>> import fdf
    >>> nstx = fdf.Machine('nstx')
    >>> nstx.s140000.logbook()
    >>> nstx.addshots(xp=1048)
    >>> nstx.s140001.mpts.plot()

"""


import importlib as _importlib
import pkgutil as _pkgutil

__all__ = [_mod[1].split(".")[-1] for _mod in
           filter(lambda _mod: _mod[1].count(".") == 1 and not
                               _mod[2] and __name__ in _mod[1],
                  [_mod for _mod in _pkgutil.walk_packages("." + __name__)])]

__sub_mods__ = [".".join(_mod[1].split(".")[1:]) for _mod in
                filter(lambda _mod: _mod[1].count(".") > 1 and not
                                    _mod[2] and __name__ in _mod[1],
                       [_mod for _mod in
                        _pkgutil.walk_packages("." + __name__)])]
from . import *
from factory import Machine

for _module in __sub_mods__:
    _importlib.import_module("." + _module, package=__name__)

