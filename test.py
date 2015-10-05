# -*- coding: utf-8 -*-

import fdf

nstx = fdf.Machine('nstx')
nstx.addshot(140000)
nstx.logbook(140000)
sl = nstx.get_shotlist(xp=1048, verbose=True)
nstx.addshot(xp=1048)
    