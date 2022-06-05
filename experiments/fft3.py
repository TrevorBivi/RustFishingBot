from scipy.fft import fft, ifft
from scipy.fft import fft, fftfreq


import numpy as np
import os
from PIL import Image
import PIL
#import pygame
import io
import time as t
from math import *
#from pygame.locals import *
import math as m
from nfft import nfft, ndft
import sys
import random as rnd
#from basicHelpers import *
#from persp_proj_tests import *

MAX_PAS_VAL_MUL = 60

dbg_time = t.time()
def dbg(msg, lvl=0):
    pid = os.getpid()
    if lvl >= 1:
        global dbg_time
        nt = t.time()
        msg = str(pid) + ' ' + str(nt-dbg_time) + ' -- ' + msg
        print(pid, nt-dbg_time, '--', msg)
        sys.stdout.flush()
        dbg_time = nt
    with open('pid' + str(pid) + '_dbg.txt','a+') as dbgf:
        dbgf.write( msg + '\n' )

rod_map_im = Image.open(r"C:\Users\Monchy\Documents\RustFishingBot\rust\1440p_quality2\rod_mapv2.png")
frequent_rod_points = []
rod_map_offset = 346+1596, 114+735
for x in range(rod_map_im.size[0]):
    for y in range(rod_map_im.size[1]):
        if rod_map_im.getpixel((x,y)) == (255,255,255):
            frequent_rod_points.append((x+rod_map_offset[0],y+rod_map_offset[1]))

def sdist(p1,p2):
    return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2

def rod_sdist(pos):
    best = 999999
    for rp in frequent_rod_points:
        new_dist = sdist(pos,rp) ** 0.5
        best = min(best, new_dist)
    return max(1,best)

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

    '''if debug:
        plt.title('band_fft')
        plt.plot(k, f_x, label='fx')
        plt.plot(k, f_y, label='fy')
        plt.show()'''
    
    return f_x, f_y, k

def band_shake(f_xy, var):
    debug = False#True

    intensities = [var['freq_0'],var['freq_1'],var['freq_2'],var['freq_3'],var['freq_4'],var['freq_5'],var['freq_6'], var['freq_7']]
    offsets = [var['freq_0b'],var['freq_1b'],var['freq_2b'],var['freq_3b'],var['freq_4b'],var['freq_5b'],var['freq_6b'], var['freq_7b']]
    xy_shake = 0
    for i in range( min(len(f_xy), len(intensities)) ):
        xy_shake += (f_xy[i] - offsets[i]) * intensities[i]
    '''
    if debug:
        plt.title('band_shake')
        xaxis = [i for i in range(len(f_x))]
        plt.plot(xaxis[:len(intensities)],intensities)
        plt.plot(xaxis, f_xy)
        plt.show()'''

    return xy_shake# + y_shake
            

class Fisht:
    def __init__(self, sesh, var):#)passval, timescore = 0, bin2score = 1, overshootp=1):
        self.var = var
        self.sesh = sesh
        self.swung = False
        if len(sesh) and len(sesh[0]) and len(sesh[0][0]) >= 2:
            self.time = sesh[0][0][2]
        else:
            self.time = 0
        self.timescores = []
        self.swing_time = None

    def score(self,iter_dat, time_change, swing_frame):
        dbg('@Fisht.score')

        if len(iter_dat) < 16:
            return

        latest_pos = iter_dat[-1]
        dist_score = rod_sdist(latest_pos)
        dist_score = self.var['dist_m'] * (dist_score - self.var['dist_0'])
        dist_score = min(dist_score, self.var['dist_max_punishment'])
        
        # 2 time variables
        #

        #f_xy = fx * (self.var['xy_ratio']) + fy * (1-self.var['xy_ratio'])
        f_x,f_y, fa = band_fft(iter_dat, self.var['avg_pos'])
        #print('retted',fftret)
        shake_x =  band_shake(f_x, self.var)
        shake_y =  band_shake(f_y, self.var)
        keep_x = shake_x > 0
        keep_y = shake_y > 0

        if keep_x and keep_y:
            ft_val = shake_x * (self.var['xy_ratio']) + shake_y * (1-self.var['xy_ratio'])
        #5 freq variables
        if keep_x:
            ft_val = shake_x
        elif keep_y:
            ft_val = shake_y
        else:
            ft_val = 0


        val = ft_val + dist_score

        #self.timescores.append( val )
        '''
        #2 scoring variables
        if val > self.var['min_trigger_val']:
            self.cur_score += min(self.var['overshoot_cap'] * self.var['min_trigger_val'] , self.var['min_trigger_val'] + (val - self.var['min_trigger_val']) * self.var['overshootp'])

            if self.cur_score > self.var['min_trigger_val'] * MAX_PAS_VAL_MUL: #todo move into inc
                dbg('%Fisht.score - overscore')
                return True'''
        self.timescores.append( (self.time, val) )
        dbg('%Fisht.score ')

    def fish(self):
        dbg('@fish')
        for iter in self.sesh:
            new_time = iter[-1][2] - self.sesh[0][0][2]
            #assert new_time != self.time
            time_change = new_time - self.time
            self.time = new_time#iter[-1][2] - self.sesh[0][0][2]
            
            if not self.swung and iter[-1][0] < self.var['max_swing']:
                self.swung = True
                self.swing_time = self.time
                self.score(iter[-self.var['samples']:], time_change, True)
            else:
                self.score(iter[-self.var['samples']:], time_change, False)

        dbg('%fish')
            
#x = np.linspace(0.0, N*T, N, endpoint=False)
#y = np.sin(50.0 * 2.0*np.pi*x) + 0.5*np.sin(80.0 * 2.0*np.pi*x)
#yf = fft(y)
#xf = fftfreq(N, T)[:N//2]
#plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
#plt.grid()
#plt.show()

def cut(sesh, amnt):
    end_time = sesh[-1][-1][2]
    poss = []
    for pos in sesh:
        if end_time - pos[-1][2] < amnt:
            break
        poss.append(pos)
    return poss

def check_var(var, nosim_var, snap_points, catch_points):
    #print('SIM START')
    #sys.stdout.flush()
    dbg('@check_var')
    t1 = t.time()
    fshs = []
    for cp in catch_points:
        cp = cut(cp, 0.8)
        fsh = Fisht(cp, var)
        fsh.fish()
        fshs.append(fsh)
    dbg('&check_var - done catch',1)
    sfshs = []
    for sp in snap_points:
        sp = cut(sp, 4.4)
        fsh = Fisht(sp, var)
        fsh.fish()
        sfshs.append(fsh)
    dbg('&check_var - done snap',1)
    t2 = t.time()
    def score(timescore, overshootp, overshoot_cap, min_trigger_val, time_m, time_0, time_change):
        #dbg('&check_var.score ',0)
        raw_score = timescore[1]
        raw_score += time_m * (timescore[0]-time_0)
        if raw_score < min_trigger_val:
            return 0
        return min(overshoot_cap, (min_trigger_val + (raw_score - min_trigger_val) * overshootp)) * time_change / (1/31.72751516580092)
    #print('SIM END')
    #sys.stdout.flush()
    dbg('&check_var - maxpassloop',1)
    all_objs = []
    for overshootp in nosim_var['overshootp']:
        dbg('&check_var - overshootp loop',0)
        for overshoot_cap in nosim_var['overshoot_cap']:
            for swing_max in nosim_var['swing_max']:
                for swing_m in nosim_var['swing_m']:
                    for swing_0 in nosim_var['swing_0']:
                        for min_trigger_val in nosim_var['min_trigger_val']:
                            for time_m in nosim_var['time_m']:
                                for time_0 in nosim_var['time_0']:
                                    dbg('&check_var - time0 loop',0)
                                    max_objs = []
                                    max_passs = nosim_var['max_pass']
                                    dbg('&check_var - maxpass build',0)
                                    for max_pass in max_passs:
                                        max_objs.append({
                                            'nosim_var':{
                                                'overshootp': overshootp,
                                                'overshoot_cap':overshoot_cap,
                                                'min_trigger_val': min_trigger_val,
                                                'time_m': time_m,
                                                'time_0': time_0,
                                                'max_pass': max_pass,
                                                'swing_max':swing_max,
                                                'swing_0':swing_0,
                                                'swing_m':swing_m},
                                            'var': var,
                                            'catch_err': 0,
                                            'catch_scc': 0,
                                            'snap_err': 0,
                                            'snap_scc': 0,
                                            'catch_times':[],
                                            'snap_times': []
                                        })
                                    dbg('&check_var - cfishbuild',0)
                                    for fsh in fshs:
                                        cur_score = 0
                                        cur_max_i = 0
                                        if len(fsh.timescores): # wasnt needed?
                                            cur_time = fsh.timescores[0][0]
                                        else:
                                            cur_time = 0
                                        for ts in fsh.timescores:
                                            new_time = ts[0]
                                            time_change = new_time - cur_time
                                            cur_time = new_time
                                            cur_score += score(ts, overshootp, overshoot_cap, min_trigger_val, time_m, time_0, time_change)
                                            if ts[0] == fsh.swing_time:
                                                cur_score += max(-swing_max,swing_m * (ts[0] - swing_0))
                                            while cur_score > max_passs[cur_max_i]:
                                                max_objs[cur_max_i]['catch_err'] += 1
                                                max_objs[cur_max_i]['catch_times'].append(ts[0])
                                                cur_max_i += 1
                                                if cur_max_i >= len(max_objs):
                                                    break
                                            if cur_max_i >= len(max_objs):
                                                    break
                                        else:
                                            for mi in range(cur_max_i, len(max_objs)):
                                                max_objs[mi]['catch_scc'] += 1
                                    
                                    dbg('&check_var - sfishbuild',0)
                                    for fsh in sfshs:
                                        cur_score = 0
                                        cur_max_i = 0
                                        if len(fsh.timescores):
                                            cur_time = fsh.timescores[0][0]
                                        else:
                                            cur_time = 0
                                        for ts in fsh.timescores:
                                            new_time = ts[0]
                                            time_change = new_time - cur_time
                                            cur_time = new_time
                                            cur_score += score(ts, overshootp, overshoot_cap, min_trigger_val, time_m, time_0, time_change)
                                            if ts[0] == fsh.swing_time:
                                                cur_score += max(-swing_max,swing_m * (ts[0] - swing_0))
                                            while cur_score > max_passs[cur_max_i]:
                                                max_objs[cur_max_i]['snap_scc'] += 1
                                                max_objs[cur_max_i]['snap_times'].append(ts[0])
                                                cur_max_i += 1
                                                if cur_max_i >= len(max_objs):
                                                    break
                                            if cur_max_i >= len(max_objs):
                                                    break
                                        else:
                                            for mi in range(cur_max_i, len(max_objs)):
                                                max_objs[mi]['snap_err'] += 1
                                    all_objs += max_objs
                                    dbg('&check_var - maxobj finish',0)
                                    for max_obj in max_objs:
                                        max_obj['catch_times'] = sum(max_obj['catch_times']) / len(max_obj['catch_times'])
                                        max_obj['catch_ratio'] = max_obj['catch_err'] / max(1,max_obj['catch_scc'])
                                        max_obj['snap_ratio'] = max_obj['snap_err'] / max(1,max_obj['snap_scc'])
                                        max_obj['snap_times'] = sum(max_obj['snap_times']) / len(max_obj['snap_times'])
                                    
    dbg('%check_var',1)
    return all_objs
'''
DEF_VAR = {'freq_0': -0.0978,
'freq_1': -0.06541789551073039,
'freq_2': -0.030205145627117902,
'freq_3': -0.019440457004569516,
'freq_4': 0.018721640315573582,
'freq_5': 0.5383483025096063,
'freq_6': 1.027098212947675,
'freq_7': 0.8590194161679364,
'freq_0b': 2,
'freq_1b': 1,
'freq_2b': 0.5,
'freq_3b': 0.10738641913899184,
'freq_4b': 0.1,
'freq_5b': 0.1,
'freq_6b': 0.3,
'freq_7b': 0.2,
'xy_ratio': 0.3316214575292773,
'samples': 16,
'avg_pos': True,
'max_swing': 1850,
'dist_m': 0.34098306169114306,
'dist_0': 8,
'dist_max_punishment': 1.8020323850221842}

DEF_NOSIM_VAR = {'overshootp': 0.10418095724782138,
'overshoot_cap': 21.213316706386966,
'min_trigger_val': 19.682860979593897,
'time_m': 1.5741077123412792,
'time_0': 2.570777144690224,
'max_pass': 574.4988714104833,
'swing_max': 229.27259366963978,
'swing_0': 0.6724578776057624,
'swing_m': -111.60311752979196}
'''

#DEF_VAR = {'freq_0': -0.09329156912662259, 'freq_1': -0.06541789551073039, 'freq_2': -0.030205145627117902, 'freq_3': -0.019440457004569516, 'freq_4': 0.018721640315573582, 'freq_5': 0.5383483025096063, 'freq_6': 1.027098212947675, 'freq_7': 0.8590194161679364, 'freq_0b': 2.2031168816454576, 'freq_1b': 1.0704839609120984, 'freq_2b': 0.5, 'freq_3b': 0.10738641913899184, 'freq_4b': 0.1, 'freq_5b': 0.1, 'freq_6b': 0.3, 'freq_7b': 0.2, 'xy_ratio': 0.3316214575292773, 'samples': 16, 'avg_pos': True, 'max_swing': 1850, 'dist_m': 0.34098306169114306, 'dist_0': 8, 'dist_max_punishment': 1.8020323850221842}

#DEF_NOSIM_VAR = {'overshootp': 0.09740053614449569, 'overshoot_cap': 19.646411765812463, 'min_trigger_val': 19.682860979593897, 'time_m': 1.5825469173602915, 'time_0': 2.774076771582799, 'max_pass': 550.8287165308077, 'swing_max': 251.79398332364622, 'swing_0': 0.6133397719795058, 'swing_m': -122.34785104202247}

DEF_NOSIM_VAR = {"overshootp": 0.09740053614449569, "overshoot_cap": 19.646411765812463, "min_trigger_val": 19.682860979593897, "time_m": 1.5825469173602915, "time_0": 2.534404459078796, "max_pass": 550.8287165308077, "swing_max": 251.79398332364622, "swing_0": 0.6133397719795058, "swing_m": -122.34785104202247}
DEF_VAR = {"freq_0": -0.09329156912662259, "freq_1": -0.06541789551073039, "freq_2": -0.030205145627117902, "freq_3": -0.019440457004569516, "freq_4": 0.018721640315573582, "freq_5": 0.5200235026305314, "freq_6": 1.027098212947675, "freq_7": 0.8590194161679364, "freq_0b": 2.2031168816454576, "freq_1b": 1.1431150381788198, "freq_2b": 0.5, "freq_3b": 0.11673739602607798, "freq_4b": 0.1, "freq_5b": 0.1, "freq_6b": 0.3, "freq_7b": 0.2, "xy_ratio": 0.3316214575292773, "samples": 16, "avg_pos": True, "max_swing": 1850, "dist_m": 0.34098306169114306, "dist_0": 8, "dist_max_punishment": 1.8020323850221842}
DEF_NOSIM_VAR = {"overshootp": 0.09740053614449569,
 "overshoot_cap": 19.646411765812463,
 "min_trigger_val": 19.3666595474395,
 "time_m": 1.5825469173602915,
 "time_0": 2.534404459078796,
 "max_pass": 550.8287165308077,
 "swing_max": 236.90883454731426,
 "swing_0": 0.6133397719795058,
 "swing_m": -116.92675914903617}
DEF_VAR = {"freq_0": -0.09329156912662259,
 "freq_1": -0.06541789551073039,
 "freq_2": -0.030205145627117902,
 "freq_3": -0.020517108811970514,
 "freq_4": 0.018721640315573582,
 "freq_5": 0.5200235026305314,
 "freq_6": 1.027098212947675,
 "freq_7": 0.8322699144747574,
 "freq_0b": 2.2031168816454576,
 "freq_1b": 1.0489240897032903,
 "freq_2b": 0.5,
 "freq_3b": 0.11673739602607798,
 "freq_4b": 0.1,
 "freq_5b": 0.1,
 "freq_6b": 0.3,
 "freq_7b": 0.2,
 "xy_ratio": 0.3316214575292773,
 "samples": 16,
 "avg_pos": True,
 "max_swing": 1850,
 "dist_m": 0.34098306169114306,
 "dist_0": 8,
 "dist_max_punishment": 1.8020323850221842}


#DEF_VAR = {"freq_0": -0.08529156912662259, "freq_1": -0.06348161746358668, "freq_2": -0.025205145627117902, "freq_3": -0.015517108811970514, "freq_4": 0.018099252840634853, "freq_5": 0.4704342680549147, "freq_6": 0.907098212947675, "freq_7": 0.7365181792352137, "freq_0b": 2.1380983695476816, "freq_1b": 0.9720543668184644, "freq_2b": 0.45077839906202544, "freq_3b": 0.11673739602607798, "freq_4b": 0.1, "freq_5b": 0.1, "freq_6b": 0.37095383375272595, "freq_7b": 0.19419247803598078, "xy_ratio": 0.35288387577976776, "samples": 16, "avg_pos": True, "max_swing": 1850, "dist_m": 0.34098306169114306, "dist_0": 11.201302854935287, "dist_max_punishment": 1.6342425209450926}
#DEF_NOSIM_VAR = {"overshootp": 0.09373619562610261, "overshoot_cap": 19.646411765812463, "min_trigger_val": 18.6, "time_m": 1.623864587506146, "time_0": 2.611442146483848, "max_pass": 501.66698839835766, "swing_max": 260.9097966581453, "swing_0": 0.5013140024252769, "swing_m": -109.03779379188593} 

DEF_NOSIM_VAR = {"overshootp": 0.08595498174498853, "overshoot_cap": 21.451453088110707, "min_trigger_val": 17.810190260493645, "time_m": 1.7032067459377087, "time_0": 2.8477544868608753, "max_pass": 515.5354978252527, "swing_max": 260.9097966581453, "swing_0": 0.4859284299467171, "swing_m": -118.13309942782979}
DEF_VAR = {"freq_0": -0.07933572832789543, "freq_1": -0.0685796987035314, "freq_2": -0.0252051456271179, "freq_3": -0.017707085800931065, "freq_4": 0.018099252840634853, "freq_5": 0.48584362721141383, "freq_6": 0.907098212947675, "freq_7": 0.6846131166115145, "freq_0b": 2.160187253276379, "freq_1b": 0.9720543668184644, "freq_2b": 0.45077839906202544, "freq_3b": 0.11673739602607798, "freq_4b": 0.1, "freq_5b": 0.11002481011704779, "freq_6b": 0.37095383375272595, "freq_7b": 0.19419247803598078, "xy_ratio": 0.35288387577976776, "samples": 16, "avg_pos": True, "max_swing": 1850, "dist_m": 0.34098306169114306, "dist_0": 11.201302854935287, "dist_max_punishment": 1.6342425209450926}

#DEF_VAR = {'dist_0': 8,),
# 'dist_max_punishment': (1.861471367743273,), 'freq_intensities': ([1.228223230387568, 1.1827098212947675, 0.5981545326464557, 0.0],), 'overshoot_cap': (1.0936761758120748,), 'time_m': (1.3879031118965048,), 'high_freq_intensities': ([0.09523959738528029, 0.06376921967955657],), 'xy_ratio': (0.3316214575292773,), 'swing_m': (-94.85958811023119,), 'swing_0': (0.7393364159479834,), 'overshootp': (0.13682207651298983,), 'min_trigger_val': (12.72896316127042,), 'time_0': (2.9209354307544984,), 'dist_m': (0.3,)}

#DEF_VAR = {'freq_0': -0.09329156912662259, 'freq_1': -0.0676770171271879, 'freq_2': -0.030205145627117902, 'freq_3': -0.020517108811970514, 'freq_4': 0.022099252840634853, 'freq_5': 0.5294342680549147, 'freq_6': 1.027098212947675, 'freq_7': 0.8165181792352137, 'freq_0b': 2.1380983695476816, 'freq_1b': 1.0489240897032903, 'freq_2b': 0.5, 'freq_3b': 0.11673739602607798, 'freq_4b': 0.1, 'freq_5b': 0.1, 'freq_6b': 0.37095383375272595, 'freq_7b': 0.19419247803598078, 'xy_ratio': 0.35288387577976776, 'samples': 16, 'avg_pos': True, 'max_swing': 1850, 'dist_m': 0.34098306169114306, 'dist_0': 11.201302854935287, 'dist_max_punishment': 1.6342425209450926}

#DEF_NOSIM_VAR = {'overshootp': 0.09373619562610261, 'overshoot_cap': 19.646411765812463, 'min_trigger_val': 20.310915087376674, 'time_m': 1.623864587506146, 'time_0': 2.611442146483848, 'max_pass': 501.66698839835766, 'swing_max': 265.1261930874385, 'swing_0': 0.5013140024252769, 'swing_m': -109.03779379188593}
{'catch_ratio': 0.234375, 'snap_ratio': 0.024}

def check_vars( params):
    dbg('@check_vars',1)
    iters, nosim_iters, snap_points, catch_points = params[:]
    sys.stdout.flush()
    values = {}
    indexs = {}
    total = 1
    for key, value in iters.items():
        #print('KV',key,value)
        indexs[key] = 0
        values[key] = value
        total *= len(value)


    keys = tuple(iters.keys())
    done = False
    amnt = 0
    all = []
    #func_start = t.time()
    while not done:
        mod = {}
        
        dbg('&check_vars - loop 1' + str(amnt) + '/' + str(total) + '=' + str(amnt/total),1)
        amnt += 1
        for key in keys:
            mod[key] = iters[key][indexs[key]]
        dbg('&check_vars - loop 2',1)
        use_var = {**DEF_VAR, **mod}
        dbg('&check_vars - loop 3',1)
        all += check_var(use_var, nosim_iters, snap_points, catch_points)
        dbg('&check_vars - loop 4',1)
        for i in range(len(keys)):
            indexs[keys[i]] += 1
            if indexs[keys[i]] == len(values[keys[i]]):
                indexs[keys[i]] = 0
            else:
                break
        else:
            done = True
        dbg('&check_vars - loop 5 -- ' + str(done),1)
        #if amnt % 4 == 0 and amnt != 0 and amnt != 128:
        #    print(amnt, '/' , total , '=' , amnt/total, ' *' ,  (total-amnt) / (amnt/(t.time()-func_start))/60 , 'm'  )
    #print(all)
    dbg('%check_vars',1)
    return all



#check_vars({'time_0':(1,2,3), 'samples':(6,7,8)} , 10, 100, 20)

if __name__ == '__main__':
    from turtle import color
    import matplotlib.pyplot as plt
    import json
    from multiprocessing import Pool
    catch_points = []
    catch_dict = {}
    rec_times = []
    rec_lens = []
    
    all = []
    with open('dbg\\catches.txt', 'r') as ff:
        dat = ff.read()
        points = []
        for s in dat.split('\n'):
            if len(s):
                obj = json.loads(s)
                rec_times.append(obj[1][-1][-1][2] - obj[1][0][0][2])
                rec_lens.append(len(obj[1]))
                catch_points.append(obj[1])
                catch_dict[obj[0]] = obj[1]
                
                #if len(snap_points) > 2:
                    #print('snap_pppp', snap_points[0][2])
                    #snap_lengths.append( ( snap_points[-1], abs( snap_points[-1][0][1] - snap_points[-1][-1][1] ) ))
                #break
                if len(catch_points) > 666:
                    break


    snap_points = []
    snap_lengths = []

    snap_dict = {}
    with open('dbg\\snaps.txt', 'r') as ff:
        dat = ff.read()
        points = []
        for i, s in enumerate(dat.split('\n')):
            if i == 33:
                print('33 NAME', obj[0])
            if len(s):
                obj = json.loads(s)
                
                rec_times.append(obj[1][-1][-1][2] - obj[1][0][0][2])
                rec_lens.append(len(obj[1]))

                snap_points.append(obj[1])
                snap_dict[obj[0]] = obj[1]
    
                #if len(snap_points) > 2:
                    #print('snap_pppp', snap_points[0][2])
                    #snap_lengths.append( ( snap_points[-1], abs( snap_points[-1][0][1] - snap_points[-1][-1][1] ) ))
                #break
                #if len(snap_points) > 6:
                #    break
    print('AVERAGE FRAMERATE', sum(rec_lens) / sum(rec_times))
    print('SNAPS',len(snap_points), 'CATCHES', len(catch_points))
    if 1:
        minf = 1, 50, 1
        all_variable_vars = ['xy_ratio', 'freq_0','freq_0b', 'freq_1','freq_1b', 'freq_2','freq_2b', 'freq_3','freq_3b', 'freq_4','freq_4b', 'freq_5','freq_5b', 'freq_6','freq_6b', 'freq_7','freq_7b', 'dist_m', 'dist_0', 'dist_max_punishment']
        all_nosim_vars = ['time_m', 'time_0','overshootp', 'overshoot_cap', 'max_pass', 'min_trigger_val', 'swing_max', 'swing_m', 'swing_0',]

        fixed_vars = {
            #'freq_intensities':[
            #    [1.3,1,0.6,0],
            #],
            #'overshoot_cap':(1,1.05,1.075)
        }
        iter_size = 0.1
        best_var = DEF_VAR
        best_score = None
        best_nosim_var = DEF_NOSIM_VAR
        print('preloop',best_var)
        best_score = 99
        new_ds = None
        while True:
            var_lists_low = {}
            var_lists_high = {}
            variable_vars = all_variable_vars[:]

            amnt_proc = 2
            var_lists = [{}] * amnt_proc

            #USE LAST DELTA
            if new_ds:
                print(" #USING LAST DS:")
                for i in range(amnt_proc):
                    for variable_var in all_variable_vars:
                        if variable_var in new_ds.keys():
                            if type(new_ds[variable_var]) == list:
                                var_lists[i][variable_var] = (best_var[variable_var],)
                                news = []
                                ds = []
                                for j in range(len( new_ds[variable_var] )):
                                    if new_ds[variable_var][j] != 0:
                                        var_lists[i][variable_var] = [
                                            [ best_var[variable_var][j] for j in range(len(new_ds[variable_var])) ],
                                            [ best_var[variable_var][j] + new_ds[variable_var][j] * rnd.uniform(-0.2, 0.7) for j in range(len(new_ds[variable_var])) ],
                                            [ best_var[variable_var][j] + new_ds[variable_var][j] * rnd.uniform(0.5, 0.9) for j in range(len(new_ds[variable_var])) ]
                                        ]
                                        break
                                else:
                                    var_lists[i][variable_var] = (best_var[variable_var],)                            
                            
                            elif new_ds[variable_var] != 0:
                                var_lists[i][variable_var] = (best_var[variable_var] + new_ds[variable_var] * 0.5 * rnd.uniform(-0.2,1), best_var[variable_var] + new_ds[variable_var] * rnd.uniform(0.1,1))
                            else:
                                var_lists[i][variable_var] = (best_var[variable_var],)
                        else:
                            var_lists[i][variable_var] = (best_var[variable_var],)
                
                #print(var_lists_low, var_lists_high)
            else:
                var_lists = []
                #MOD
                for i in range(amnt_proc):
                    var_lists.append({})
                    variable_vars = all_variable_vars[:]
                    #DONT MOD
                    print(" #USING PREV")
                    for o in range(len(all_variable_vars) - 3):
                        ro = rnd.randint(0, len(variable_vars) -1)
                        if variable_vars[ro] in []:#['dist_m', 'dist_0', 'dist_max_punishment', 'overshoot_cap']:
                            ro = rnd.randint(0, len(variable_vars) -1)
                            #if var_lists in ['dist_m', 'dist_0', 'dist_max_punishment', 'overshoot_cap']:
                            #    ro = rnd.randint(0, len(var_lists) -1)
                        print(variable_vars[ro], i, ro,',', end = '')
                        # print('dbg',var_lists,i,ro, best_var)
                        var_lists[i][variable_vars[ro]] = (best_var[variable_vars[ro]], )
                        var_lists[i][variable_vars[ro]] = (best_var[variable_vars[ro]], )
                        del variable_vars[ ro ]

                    for variable_var in variable_vars:
                        if rnd.randint(0,2)== 0:
                            rand1 = rnd.uniform(0.15, 1)
                            rand2 = -rnd.uniform(0.15, 1)
                        else:
                            rand1 = rnd.uniform(0.15,0.55)
                            rand2 = -rnd.uniform(0.15,0.55)
                        
                        if variable_var == 'freq_intensities' or variable_var == 'high_freq_intensities':
                            index = rnd.randint(0,len(best_var[variable_var])-1)
                            print('  - modding list', variable_var, index, ' +- ', rand1 * iter_size, rand2 * iter_size)
                            
                            best_val = best_var[variable_var][index]
                            
                            new_1 = best_val - DEF_VAR[variable_var][index] * iter_size * rand1
                            new_2 = best_val + DEF_VAR[variable_var][index] * iter_size * rand2
                            
                            new_list_1 = best_var[variable_var][:]
                            new_list_2 = best_var[variable_var][:]

                            new_list_1[index] = new_1
                            new_list_2[index] = new_2
                            print("OLLDDD!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            #var_lists[i][variable_var] = (new_list_1, best_var[variable_var] + ) * rnd.uniform, new_list_2)
                        else:
                            print(' - modding item', i, variable_var, ' +- ', rand1 * iter_size, rand2 * iter_size,'   of ',best_var[variable_var])

                            #var_lists[i][variable_var] = (best_var[variable_var], best_var[variable_var] + DEF_VAR[variable_var] * iter_size * rand1, best_var[variable_var] + DEF_VAR[variable_var] * iter_size * rand2)
                            var_lists[i][variable_var] = (best_var[variable_var] + (1 - (amnt_proc % 3)) * best_var[variable_var] * rnd.uniform(-0.15, 0.15), best_var[variable_var] - DEF_VAR[variable_var] * iter_size * rand1, best_var[variable_var] - DEF_VAR[variable_var] * iter_size * rand2)
            
            #FIXED
            for i in range(amnt_proc):
                for fixed_var_key, fixed_var_value in fixed_vars.items():
                    print('  - fixed ',fixed_var_key)
                    var_lists[i][fixed_var_key] = fixed_var_value


            nosim_vars = []
            rands = [rnd.randint(0,2) for i in range(len(all_nosim_vars))]
            for i in range(amnt_proc):
                nosim_vars.append({})
                for j, nosim_var_name in enumerate(all_nosim_vars):
                    cur = best_nosim_var[nosim_var_name]
                    if nosim_var_name in ('max_pass','min_trigger_val') or rands[j] == 0:
                        orig = DEF_NOSIM_VAR[nosim_var_name]
                        nosim_vars[-1][nosim_var_name] = [ cur - orig * rnd.uniform(0.01,iter_size) ,cur, cur + orig * rnd.uniform(0.01,iter_size)]
                    else:
                        nosim_vars[-1][nosim_var_name] = [cur, ]

            print('')
            def p(v,nsv):
                print('  > making')
                print('    ', v)
                print('    ', nsv)
                return (v, nsv, snap_points, catch_points)
            inps = [p(vv,nsvv) for vv,nsvv in zip(var_lists,nosim_vars)]

            print('>start procs')
            with Pool(amnt_proc) as p:
                res = p.map(check_vars, inps)
            print('>procs ended')
            all = []
            for r in res:
                all += r
            #print(all)

            all.sort(key=( lambda x: x['snap_ratio'] + 0.333 * x['catch_ratio'] ))

            #with open('simres.txt', 'a+') as simfile:
            #    for a in all:
            #        simfile.write(json.dumps(a) + '\n')

            new_best = all[0]
            
            new_score = new_best['snap_ratio'] + 0.333 * new_best['catch_ratio']
            
            print("&& ret vals:",len(all))
            for i in range(4):
                print(all[int(new_score < best_score)+i])

            
            if new_score < best_score:
                new_ds = {}
                print('$$ NEW:', new_score)
                print( 'DEF_VAR=',new_best['var'] )
                print( 'DEF_NOSIM_VAR=',new_best['nosim_var'] )
                best_stats = {'catch_ratio':new_best['catch_ratio'], 'snap_ratio': new_best['snap_ratio']}
                print(best_stats)
                print()
                for variable_vars in all_variable_vars:
                    #print('FOR ', variable_var, 'IN', all_variable_vars)
                    #print('    ')
                    if type(new_best['var'][variable_var]) == list:
                        new_ds[variable_var] = [new - best for new, best in zip(new_best['var'][variable_var], best_var[variable_var])]
                    else:
                        new_ds[variable_var] = new_best['var'][variable_var] - best_var[variable_var]

                best_score = new_score
                best_nosim_var = new_best['nosim_var']
                
                best_var = new_best['var']
                
                with open('dbg/simtests.txt', 'a+') as file:
                    file.write(json.dumps( {'run':'a111', 'data':new_best} ) + '\n')
            else:
                new_ds = None
                print('$$ KEEPING:',best_score)
                print( 'DEF_VAR=',new_best['var'] )
                print( 'DEF_NOSIM_VAR=',new_best['nosim_var'] )
                print(best_stats)
                print()
            
        
        raise Exception('stop')
        vars1 = {
            'overshootp': (0.15,0.1666,0.18,),
            'min_trigger_val':(10.5,11,11.5),

            'freq_intensities':[[1.3,1,0.6],],
            'max_large_freq':(150,160,170,180,200),
            'time_m':(1.0, 1.15, 1.3),
            'time_0':(2.3,),

            'xy_ratio': (0.35, 0.45,),
            'samples':(16,),
            'avg_pos': (True, )
        }

        vars2 = {
            'overshootp': (0.15,0.1666,0.18),
            'min_trigger_val':(10.5,11,11.5),

            'freq_intensities':[[1.2,1,0.6],],
            'max_large_freq':(150,160,170,180,200),
            'time_m':(1.0, 1.15, 1.3),
            'time_0':(2.3,),

            'xy_ratio': (0.35, 0.45,),
            'samples':(16,),
            'avg_pos': (True, )
        }

        vars3 = {
            'overshootp': (0.15,0.1666,0.18),
            'min_trigger_val':(10.5,11,11.5),

            'freq_intensities':[[1.2,1,0.7],],
            'max_large_freq':(150,160,170,180,200),
            'time_m':(1.0, 1.15, 1.3),
            'time_0':(2.3,),

            'xy_ratio': (0.35, 0.45,),
            'samples':(16,),
            'avg_pos': (True, )
        }
        
        minf = 14, 70, 2

        def p(v):
            return (v, *minf, snap_points, catch_points)

        inps = (p(vars1), p(vars2), p(vars3))

        '''all = check_vars(inps[0])

        for catch_mult in (0,0.1,0.2,0.4):
            print('catch_mult================', catch_mult)
            all.sort(key=( lambda x: x['snap_ratio'] + catch_mult * x['catch_ratio'] ))
            print('sortlen', len(all))
            for i in range(8):
                if len(all) <= i:
                    break
                print(type(all[i]), all[i])


        raise Exception('stop')'''
        print('start procs')
        with Pool(3) as p:
            res = p.map(check_vars, inps)
        
        all = []
        for r in res:
            all += r
        print(all)

        for catch_mult in (0,0.1,0.2,0.4):
            print('catch_mult================', catch_mult)
            all.sort(key=( lambda x: x['snap_ratio'] + catch_mult * x['catch_ratio'] ))
            print('sortlen', len(all))
            for i in range(16):
                if len(all) <= i:
                    break
                print(type(all[i]), all[i])
        raise Exception('stop')
    
    cutt = 16
    for cutt in range(20,30,2):
        avgsx = [0] * (cutt//2)
        avgsy = [0] * (cutt//2)
        sampless = 0
        averages_iter = []
        samples_iter = []
        for sesh in catch_points:
            for iti, iter in enumerate(sesh):
                if iti >= len(averages_iter):
                    samples_iter.append([0] * (cutt//2))
                    averages_iter.append(0)
                if len(iter) > cutt:
                    f_x, f_y, f_t = band_fft( iter[-cutt:] )
                    for i in range(cutt//2-1, cutt//2):
                        avgsx[i] += f_x[i]
                        avgsy[i] += f_y[i]
                        samples_iter[iti][i] += f_y[i]
                    averages_iter[iti] += 1
                    sampless += 1
                        #print('calc avg')
        avgs_per = []
        for avgs, samples in zip(averages_iter, samples_iter):
            avged = [s / max(1,avgs) for s in samples]
            avgs_per.append(avged)
        #plt.clf()
        plt.plot([i for i in range(len(avgs_per))], avgs_per)
        #plt.title(str(cutt))
        #plt.show()
        print('avgsxaa', avgsx)
        print('avgsyaa', avgsy)
        avgsx = [ax / sampless for ax in avgsx]
        avgsy = [ay / sampless for ay in avgsy]
        print('avgsx', avgsx)
        print('avgsy', avgsy)
    plt.show()
    cutt = 16



    print('lefisher',len(snap_points))
    seshname = "844.7"

    if seshname in catch_dict.keys():
        sesh = catch_dict[seshname]
    else:
        sesh = snap_dict[seshname]
    prefixed = [filename for filename in os.listdir('E:\\tempvideo\\fisher\\') if filename.startswith(seshname)]
    print(prefixed)
    end_time = sesh[-1][-1][2] - sesh[0][0][2] - 4.1
    print(end_time)


    view_ind = 0
    view_type = 'CATCH'
    view_types = {'CATCH':catch_dict, 'SNAP':snap_dict}

    seshname = list(view_types[view_type])[view_ind]
    sesh = view_types[view_type][seshname]

    prefixed = [filename for filename in os.listdir('E:\\tempvideo\\fisher\\') if filename.startswith(seshname)]

    wiggle_var = 0.5
    playing = False
  

    WINDOW_SIZE =  600, 800
    SPEED = 0.025
    #window = pygame.display.set_mode( WINDOW_SIZE )
    clock = pygame.time.Clock()
    new = True
    while True:
        t1 = t.time()
        clock.tick(60)
        if playing:
            new = True
            end_time += SPEED
            if end_time >= sesh[-1][-1][2] - sesh[0][-1][2]:
                end_time = 0

        if new:
            view_types = {'CATCH':catch_dict, 'SNAP':snap_dict}
            print('type', view_type, 'ind', view_ind)
            seshname = list(view_types[view_type])[view_ind]
            sesh = view_types[view_type][seshname]

            prefixed = [filename for filename in os.listdir('E:\\tempvideo\\fisher\\') if filename.startswith(seshname)]
            
            new = False
            window.fill((0,0,0))
            im = None
            chosen = None
            for i, snap in enumerate(sesh):
                if end_time <= snap[-1][2] - sesh[0][0][2]:
                    im = Image.open('E:\\tempvideo\\fisher\\' + prefixed[i])
                    chosen = snap[-cutt:]
                    break
            else:
                print('SAVED CRASH')
                continue
                end_time = snap[-1][2] - sesh[0][0][2]
                chosen = sesh[0][-cutt:]
                im = Image.open('E:\\tempvideo\\fisher\\' + prefixed[-1])
    
            '''# Number of sample points
            N = len(chosen)
            # sample spacing
            print('spacing',chosen[-1][2] - chosen[0][2])
            T = N / (chosen[-1][2] - chosen[0][2])

            ay = sum([c[1] for c in chosen]) / len(chosen)
            avx = sum([c[0] for c in chosen]) / len(chosen)
            ys = [c[1] - ay for c in chosen]
            rxs = [c[0] - avx for c in chosen]
            
            xs = [c[2]- chosen[0][2] for c in chosen]
            #sss = [ x+y for x,y in zip(rxs, ys) ]

            print('SAMPLES',len(ys))
            yf = fft(np.array(ys))
            xyf = fft(np.array(rxs))
            #syf = fft(np.array(sss))

            yxf = np.fft.fftfreq(len(ys)) #fftfreq(N, T)[:N//2]
            xxf = np.fft.fftfreq(len(rxs))
            #sxf = np.fft.fftfreq(len(sss))
            #print('lenfx', len(xf) , 'yf', len(yf))'''


            '''chosen = []
            for i in range(40):
                chosen.append([ m.sin( i * 0.04 * 2 * 3.142 * 9 ) ,  m.sin( i * 0.04 * 2 * 3.142 * 9 ) , i*0.04,  ])'''
            '''
            chosen = []
            for i in range(cutt):
                chosen.append([ 42 * m.sin( i / cutt * 2 * 3.142 * 1 * wiggle_var ) + 1950 ,  12 * m.sin( i * 0.04 * 2 * 3.142 * 4 ) + 850 , i*0.05,  ])'''

            '''if len(chosen):
                avgxdat = 0
                avgydat = 0
                #nchosen = []
                for c in chosen:
                    avgxdat += c[0]
                    avgydat += c[1]
                avgxdat /= len(chosen)
                avgydat /= len(chosen)
            nchosen = []
            for c in chosen:
                xci = 0.01*(c[0] - avgxdat) + avgxdat
                yci = 0.01*(c[1] - avgydat) + avgydat
                tci = c[2]
                nchosen.append([xci,yci,tci])
            chosen = nchosen'''
            #fa = np.fft.fftfreq(len(chosen)) #np.fft.fftfreq(len(chosen))
    
            fig = plt.figure()
            N = len(chosen)


            f_x, f_y, f_t = band_fft( chosen )
            f_x0, f_y0, f_t0 = band_fft( chosen , False)
            #score = band_shake(f_x, f_y, [1,1,1])

            ax = fig.add_subplot(1, 1, 1)

            #test = power(sf,fa,0.19, 0.27)

            #if len(f_x) > 3:
            #    ax.plot( [0,1], [score, score] )
            #if len(f_x) > 3:
            #    ax.plot( [0,0.2], [test,test] )
            testfft = fft( f_x[:])
            ax.plot(f_t[:], f_y, color=(1,0.5,0.5,1))
            ax.plot(f_t[:], f_x[:], color=(0.5,0,0,1))
            ax.plot(f_t[:], f_y0, color=(0.5,0.5,1,1))
            ax.plot(f_t[:], f_x0[:], color=(0,0,0.5,1))
            
            if len(f_t) == cutt//2:
                #ax.plot(f_t[:], avgsx[:])
                #ax.plot(f_t[:], avgsy[:])
                pass
            else:
                print('fftlen', len(f_t))
            
            #ax.plot(f_t[:], f_y[:]+f_x[:])
            #ax.plot(f_t[:], abs(testfft)[:N//2])
            #ax.plot([0,0.3], [ sf[2],  sf[2]])

            time_str = chosen[-1][2] - sesh[0][-1][2]
            ax.set_ylim([0,300 * cutt / 16])
            ax.set_title(str(time_str) + '  smp ' + str(len(chosen)) + ' - ' + str(wiggle_var))
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png')
            plt.close(fig)
            figure = Image.open(img_buf)

            py_image = pygame.image.fromstring(im.tobytes(), im.size, im.mode)
            py_plot = pygame.image.fromstring(figure.tobytes(), figure.size, figure.mode)
            rect = py_image.get_rect()
            window.blit(py_image, rect)
            window.blit(py_plot, (0,260))

            if len(chosen) > 2:
                for i, pos in enumerate(chosen[:-1]):
                    print(pos)
                    pygame.draw.line(window, (255, 0, 255),(pos[0]-1596, pos[1]-735) , (chosen[i+1][0]-1596, chosen[i+1][1]-735))


        #print('time', t.time()-t1)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_d]:
                end_time += SPEED
                end_time = min(end_time, sesh[-1][-1][2] - sesh[0][-1][2])
                wiggle_var += 0.05
                new = True
            if keys[pygame.K_p]:
                playing = not playing

            elif keys[pygame.K_a]:
                end_time -= SPEED
                end_time = max(end_time, 0)
                wiggle_var -= 0.05
                new = True
            elif keys[pygame.K_s]:
                end_time = sesh[-1][-1][2] - sesh[0][0][2] - 4.1
                end_time = max(end_time, 0)
                wiggle_var = 0.5
                new = True
            elif keys[pygame.K_c]:
                end_time = sesh[-1][-1][2] - sesh[0][0][2]
                new = True
            elif keys[pygame.K_q]:
                view_ind -= 1
                new = True
            elif keys[pygame.K_e]:
                print('view_indin1',view_ind)
                view_ind += 1
                print('view_indin2',view_ind)
                new = True
            elif keys[pygame.K_w]:
                end_time = 0
                new = True
            elif keys[pygame.K_x]:
                view_type = 'CATCH'
                new = True
            elif keys[pygame.K_z]:
                view_type = 'SNAP'
                new = True

    plt.grid()
    plt.show()

    plt.clf()
    raise Exception('stop')


    x = ys#np.array([1,2,1,0,1,2,1,0]) #ys
    w = np.fft.fft(x)
    freqs = np.fft.fftfreq(len(x))

    for coef,freq in zip(w,freqs):
        if coef:
            print('{c:>6} * exp(2 pi i t * {f})'.format(c=coef,f=freq))
        plt.plot(abs(coef), freq)
    plt.show()
