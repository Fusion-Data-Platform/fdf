# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 11:50:21 2015

@author: ktritz
====
2015-Sep-1:  jcschmitt: added option to plot single timeslice using keyword 
                        option 'timeslice'
"""

import numpy as np
import matplotlib.pyplot as plt
import math as math

def plot(signal, overwrite=False, timeslice=float('NaN')):
    print(signal._name)
    if not overwrite:
        plt.figure()
    if signal._name in ['mpts', 'spline']:
        # Plot contour plots of both TE and NE for all time and radii
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
    elif not(math.isnan(timeslice)):
        # Plot the data for a single timeslice; plot all radial locations
        print("Timeslice: %f" % (timeslice))
        r = signal.radius[:]
        t = signal.time[:]
        ind_nearest_timeslice = round( (timeslice - t[0]) / (t[1] - t[0])) - 1
        plt.plot(r, signal.T[:, ind_nearest_timeslice])
    else:
        # Plot contour plot for either te or ne for all time and radii
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
