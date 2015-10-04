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
from factory import Machine  # expose facotry.Machine at package-level (DRS 10/15)
                               # e.g. >>> nstx = fdf.Machine('nstx')

for _module in __sub_mods__:
    _importlib.import_module("." + _module, package=__name__)