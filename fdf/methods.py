# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:20:43 2015

@author: ktritz
"""
import numpy as np
import matplotlib.pyplot as plt


def plot1d(data, xaxis, **kwargs):
    plt.plot(xaxis, data, **kwargs)


def plot2d(data, xaxis, yaxis, **kwargs):
    print('2D')


def plot3d(data, xaxis, yaxis, zaxis, **kwargs):
    print('3D')


def plot4d(data, xaxis, yaxis, zaxis, taxis, **kwargs):
    print('4D')

plot_methods = [None, plot1d, plot2d, plot3d, plot4d]


def plot(signal, **kwargs):
    signal[:]
    dims = signal.ndim

    multi_axis = kwargs.get('multi', None)
    if multi_axis is 'shot':
        plot_multishot(signal, **kwargs)
        return
    if multi_axis in signal.axes and dims > 1:
        plot_multi(signal, **kwargs)
        return


def plot_multi(signal, **kwargs):
    axis_name = kwargs.pop('multi', None)
    axes = [getattr(signal, axis) for axis in signal.axes]
    axis_index = signal.axes.index(axis_name)
    multi_axis = axes.pop(axis_index)
    plot_fig = plt.figure()
    ax = plt.subplot(111)
    ax.grid()
    legend = kwargs.pop('legend', False)
    for index, label in enumerate(np.asarray(multi_axis)):
        label = '{} = {:.3f} {}'.format(axis_name, label, multi_axis.units)
        data = np.take(signal, index, axis=axis_index)
        plot_axes = [np.take(axis, index, axis=axis_index)
                     if multi_axis in axis.axes else axis for axis in axes]
        plot_methods[data.ndim](data, *plot_axes, label=label, **kwargs)
    if legend:
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.subplots_adjust(right=0.65)
    plt.show()
