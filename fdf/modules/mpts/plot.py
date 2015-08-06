# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 11:50:21 2015

@author: ktritz
"""

import numpy as np
import matplotlib.pyplot as plt


def plot(signal, overwrite=False):
    print(signal._name)
    if not overwrite:
        plt.figure()
    if signal._name in ['mpts', 'spline']:
        plt.subplot(2, 1, 1)
        signal.te.plot(overwrite=True)
        plt.title(signal.te._name, fontsize=20)
        plt.ylabel('{} ({})'.format('Radius', signal.te.radius.units))
        plt.subplot(2, 1, 2)
        signal.ne.plot(overwrite=True)
        plt.title(signal.ne._name, fontsize=20)
        plt.ylabel('{} ({})'.format('Radius', signal.ne.radius.units))
        plt.xlabel('{} ({})'.format('Time', signal.ne.time.units))
        plt.suptitle('Shot #{}'.format(signal.shot), x=0.5, y=1.00,
                     fontsize=20, horizontalalignment='center')
        plt.show()
    else:
        r = signal.radius[:]
        t = signal.time[:]
        signal[:]
        t_ind = np.where(t > 0.1)[0]
        r_ind = np.where(np.logical_and(r > 30, r < 135))[0]
        sigmax = signal[t_ind.min():t_ind.max(), r_ind.min():r_ind.max(), ].max()
        plt.contourf(t, r, signal.T, levels=np.linspace(0, sigmax, 100))
        if not overwrite:
            plt.suptitle('Shot #{}'.format(signal.shot), x=0.5, y=1.00,
                         fontsize=20, horizontalalignment='center')
            plt.title(signal._name, fontsize=20)
            plt.ylabel('{} ({})'.format('Radius', signal.radius.units))
            plt.xlabel('{} ({})'.format('Time', signal.time.units))
            plt.show()
