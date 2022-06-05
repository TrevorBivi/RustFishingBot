from turtle import color
from scipy.fft import fft, ifft
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
import json
import numpy as np
import os
from PIL import Image
import PIL
import pygame
import io
import time as t
from math import *
from pygame.locals import *
import math as m
from nfft import nfft, ndft
import sys
import random as rnd
import json


def band_fft(band_positions, useAvg=True):
    debug = False#True
    start_time = band_positions[0][2]
    sample_time = band_positions[-1][2] - start_time
    N = len(band_positions)
    if N % 2 != 0:
        N -= 1
        band_positions = band_positions[1:]
    
    avg_x = 0
    avg_y = 0
    for band_position in band_positions:
        avg_x += band_position[0]
        avg_y += band_position[1]
    
    avg_x /= len(band_positions)
    avg_y /= len(band_positions)
    if useAvg == False:
        avg_x = band_positions[0][0]
        avg_y = band_positions[0][1]
    ts = []
    xs = []
    ys = []
    for band_position in band_positions:
        xs.append(band_position[0] - avg_x)
        ys.append(band_position[1] - avg_y)
        ts.append((band_position[2] - start_time) / sample_time - 0.5)
    
    f_x = abs(ndft(ts, xs)[N//2:])
    f_y = abs(ndft(ts, ys)[N//2:])
    k = np.arange(N//2)

    if debug:
        plt.title('band_fft')
        plt.plot(k, f_x, label='fx')
        plt.plot(k, f_y, label='fy')
        plt.show()
    
    return f_x, f_y, k

def band_shake(f_xy, var, dir='LOW', avg=True):
    debug = False#True

    if dir == 'LOW':
        intensities = var['freq_intensities']
    else:
        intensities = var['high_freq_intensities']

    xy_shake = 0
    #y_shake = 0
    total_intensity = 0
    #print('aaa', intensities, f_xy)
    for i in range( min(len(f_xy), len(intensities)) ):
        xy_shake += f_xy[-1-i] * intensities[i]
        #y_shake += f_y[i] * intensities[i]
        total_intensity += intensities[i]
    if avg:
        xy_shake /= total_intensity
    #xy_shake *= xy_ratio
    #y_shake /= total_intensity
    #y_shake *= (1-xy_ratio)

    if debug:
        plt.title('band_shake')
        xaxis = [i for i in range(len(f_x))]
        plt.plot(xaxis[:len(intensities)],intensities)
        plt.plot(xaxis, f_xy)
        #plt.plot(xaxis, f_y)
        #plt.plot([0,3], [x_shake + y_shake, x_shake + y_shake])
        plt.show()

    return xy_shake# + y_shake

