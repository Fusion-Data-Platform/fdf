# -*- coding: utf-8 -*-



import numpy as np
import matplotlib.pyplot as plt
import math as math

def plot(signal, overwrite=False):
    
    #if signal._name in ['bes']:
    if not overwrite:
        plt.figure()
        plt.subplot(1, 1, 1)
    plt.plot(signal.time, signal)
    if not overwrite:
        plt.suptitle('Shot #{}'.format(signal.shot), x=0.5, y=1.00,
                     fontsize=12, horizontalalignment='center')
        plt.title('BES {}'.format(signal._name), fontsize=12)
        plt.ylabel('BES {} ({})'.format(signal._name, signal.units))
        plt.xlabel('{} ({})'.format('Time', signal.time.units))
        plt.show()


