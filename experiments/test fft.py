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
#from basicHelpers import *
#from persp_proj_tests import *

MAX_PAS_VAL_MUL = 60

dbg_time = t.time()
def dbg(msg):
    return
    global dbg_time
    nt = t.time()
    print(nt-dbg_time, '--', msg)
    dbg_time = nt

def fft_snap(snap, dbg=False):
    # Number of sample points
    N = len(snap)
    # sample spacing
    #print('spacing',chosen[-1][2] - chosen[0][2])
    T = N / (snap[-1][2] - snap[0][2])
    '''avy = 0
    avx = 0
    for pos in snap:
        avy += pos[1]
        avx += pos[1]
    avy /= len(snap)
    avx /= len(snap)'''
    xs = []
    ys = []
    for pos in snap:
        ys.append(pos[1])
        xs.append(pos[0])
    if dbg:
        ax = sum(xs)/len(xs)
        ay = sum(ys)/len(ys)
        xs = [x - ax for x in xs]
        ys = [y - ay for y in ys]

    yf = fft(np.array(ys))
    xf = fft(np.array(xs))
    fa = np.fft.fftfreq(len(ys))
    axf = abs(xf)
    ayf = abs(yf)
    return axf, ayf, axf+ayf, fa

def fft_snap(snap, dbg=False):
    # Number of sample points
    N = len(snap)*3
    # sample spacing
    #print('spacing',chosen[-1][2] - chosen[0][2])
    T = N / (snap[-1][2] - snap[0][2])
    '''avy = 0
    avx = 0
    for pos in snap:
        avy += pos[1]
        avx += pos[1]
    avy /= len(snap)
    avx /= len(snap)'''
    xs = []
    ys = []
    for pos in snap:
        ys.append(pos[1])
        xs.append(pos[0])
    if dbg:
        ax = sum(xs)/len(xs)
        ay = sum(ys)/len(ys)
        xs = [x - ax for x in xs]
        ys = [y - ay for y in ys]

    yf = fft(np.array(ys))
    xf = fft(np.array(xs))
    fa = np.fft.fftfreq(len(ys))
    axf = abs(xf)
    ayf = abs(yf)
    return axf, ayf, axf+ayf, fa

def fft_snap2(snap):
    # Number of sample points
    dbg('@fft_snap2')

    if len(snap) < 6:
        return np.array([0]),np.array([0])
    if len(snap) % 2 != 0:
        snap = snap[1:]
    N = len(snap)
    T = snap[-1][2] - snap[0][2]
    fa = np.linspace(0.0, 1.0 / (2.0 * T), N // 2)

    xs = []
    ys = []
    ts = []
    #xav = 0
    #yav = 0
    for pos in snap:
        xs.append(pos[0])
        ys.append(pos[1])
        ts.append(pos[2])
    #    xav += pos[0]
    #    yav += pos[1]
    #xav /= len(pos)
    #yav /= len(pos)
    pos_ar = np.array(snap)
    ts =  [t - ts[0] for t in ts]
    dbg('&fft_snap2 - start fft')
    yf = nfft(np.array(xs), np.array(ts) )
    xf = nfft(np.array(ys), np.array(ts) )
    dbg('&fft_snap2 - end fft')
    #fa = np.fft.fftfreq(len(ys))

    ayf = abs(yf)
    axf = abs(xf)
    asf = ayf + axf
    dbg('%fft_snap2')
    return asf, fa

def power( sf, at, min_f=0, max_f = 999, midpoint=0.5, midbonus=0):
    ret = 0
    mid_f = min_f + (max_f - min_f) * midpoint
    def weight(f):
        if f < mid_f:
            w = 1 + (mid_f - f) / (mid_f - min_f) * midbonus
            return w
        w = 1 + (max_f - f) / (max_f - mid_f) * midbonus
        return w
        
    for amp, freq in zip(sf, at):
        if min_f <= freq:
            if max_f > freq:
                break
            ret += weight(freq) * amp
    return ret



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

def band_shake(f_xy, var):
    debug = False#True

    intensities = var['freq_intensities']
    
    xy_shake = 0
    #y_shake = 0
    total_intensity = 0
    #print('aaa', intensities, f_xy)
    for i in range( min(len(f_xy), len(intensities)) ):
        xy_shake += f_xy[-1-i] * intensities[i]
        #y_shake += f_y[i] * intensities[i]
        total_intensity += intensities[i]
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
            

class Fisht:
    def __init__(self, sesh, var):#)passval, timescore = 0, bin2score = 1, overshootp=1):
        self.var = var
        self.sesh = sesh
        self.cur_score = 0
        self.timescores = []
        '''#self.passval = passval
        self.passes = 0
        self.time = 0
        self.timescore = timescore
        self.bin2score = bin2score
        self.overshootp = overshootp
        '''

    def score(self,iter_dat):
        dbg('@Fisht.score')

        # 2 time variables
        time_val = self.var['time_m'] * (self.time-self.var['time_0'])
        f_x,f_y, fa = band_fft(iter_dat, self.var['avg_pos'])
        #print('retted',fftret)
        if len(f_x) < 4:
            return
        
        #f_xy = fx * (self.var['xy_ratio']) + fy * (1-self.var['xy_ratio'])

        shake_x =  band_shake(f_x, self.var)
        shake_y =  band_shake(f_y, self.var)
        keep_x = self.var['max_large_freq'] * (self.var['xy_ratio']) > shake_x
        keep_y = self.var['max_large_freq'] * (1-self.var['xy_ratio']) > shake_y

        if keep_x and keep_y:
            ft_val = shake_x * (self.var['xy_ratio']) + shake_y * (1-self.var['xy_ratio'])
        #5 freq variables
        if keep_x:
            ft_val = shake_x
        elif keep_y:
            ft_val = shake_y
        else:
            ft_val = 0


        val = ft_val + time_val

        #2 scoring variables
        if val > self.var['min_trigger_val']:
            self.cur_score += self.var['min_trigger_val'] + (val - self.var['min_trigger_val']) * self.var['overshootp']
            if self.cur_score > self.var['min_trigger_val'] * MAX_PAS_VAL_MUL: #todo move into inc
                dbg('%Fisht.score - overscore')
                return True
        self.timescores.append( (self.time, self.cur_score) )
        dbg('%Fisht.score ')

    def fish(self):
        dbg('@fish')
        for iter in self.sesh:
            self.time = iter[-1][2] - self.sesh[0][0][2]
            #1 sample variable
            if self.score(iter[-self.var['samples']:]):
                break
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

all = []


def check_var(var, min_pass_mult, max_pass_mult, iter_pass_mult, snap_points, catch_points):
    dbg('@check_var')
    fshs = []
    for cp in catch_points:
        cp = cut(cp, 0.8)
        fsh = Fisht(cp, var)
        fsh.fish()
        fshs.append(fsh)
    dbg('&check_var - done catch')
    sfshs = []
    for sp in snap_points:
        sp = cut(sp, 4.4)
        fsh = Fisht(sp, var)
        fsh.fish()
        sfshs.append(fsh)
    dbg('&check_var - done snap')
    all = []
    for max_pass in range(round(min_pass_mult*var['min_trigger_val']),round(max_pass_mult*var['min_trigger_val']),round(iter_pass_mult*var['min_trigger_val'])):
        dbg('&check_var - maxpassloop')
        catch_err = 0
        catch_scc = 0
        catch_times = []
        #nsnap = []
        #nfine = []
        t1 = t.time()
        for i, fsh in enumerate(fshs):
            if fsh.cur_score >= max_pass: # BAD
                catch_err += 1
                for ts in fsh.timescores[::2]:
                    if ts[1] >= max_pass:
                        catch_times.append(ts[0])
                        break
                #nsnap.append(i)
            else: #GOOD
                catch_scc += 1
                #nfine.append(i)

        snap_err = 0
        snap_scc = 0
        snap_times = []
        err_snaps = []
        last_snap_dbg = None
        for i, fsh in enumerate(sfshs):
            if fsh.cur_score < max_pass: #BAX
                snap_err += 1
                last_snap_dbg = i
                err_snaps.append(i)
            else: #GOOD
                for ts in fsh.timescores[::2]:
                    if ts[1] >= max_pass:
                        snap_times.append(ts[0])
                        break
                snap_scc += 1
                #nsfine.append(i)

        max_catch = max(catch_times)
        min_catch = min(catch_times)
        max_snap = max(snap_times)
        min_snap = min(snap_times)
        avt_catch = sum(catch_times)/max(1,len(catch_times))
        avt_snap = sum(snap_times)/max(1,len(snap_times))
        #if snap_err/max(1,snap_scc) < 0.022:
        #    print('ONLY SNAP FAIL = ', last_snap_dbg) #33 87
        obj = {
            'var':var,
            'max_pass':max_pass,
            'mxps':max_pass/var['min_trigger_val'],
            'snap_ratio':snap_err/max(1,snap_scc),
            'snap_time': [min_snap, avt_snap, max_snap],
            'catch_ratio': catch_err/max(1,catch_scc),
            'catch_time': [min_catch, avt_catch, max_catch]
        }

        all.append(obj)
    dbg('%check_var')
    return all

DEF_VAR = {'overshootp': 0.15505179274493416,
    'min_trigger_val': 11.801708892324534,
    'freq_intensities': [1.3316339293311987,
        1.0521287202224574,
        0.6067170495156885,
        0],
    'high_freq_intensities': [0.1,0.05], #TODO use
    'max_large_freq': 177.47244046616208,
    'time_m': 1.2661652875002063,
    'time_0': 2.48470311097795,
    'pass_mp': 38,
    'xy_ratio': 0.3316214575292773,
    'samples': 16,
    'avg_pos': True},



def check_vars( params):
    dbg('@check_vars')
    iters, min_pass_mul, max_pass_mul, iter_pass_mult, snap_points, catch_points = params
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
    func_start = t.time()
    while not done:
        mod = {}
        
        sys.stdout.flush()
        amnt += 1
        for key in keys:
            mod[key] = iters[key][indexs[key]]

        dbg('&check_vars - check var loop')
        use_var = {**DEF_VAR, **mod}
        all += check_var(use_var, min_pass_mul, max_pass_mul, iter_pass_mult, snap_points, catch_points)

        for i in range(len(keys)):
            indexs[keys[i]] += 1
            if indexs[keys[i]] == len(values[keys[i]]):
                indexs[keys[i]] = 0
            else:
                break
        else:
            done = True
        if amnt % 16 == 0 and amnt != 0 and amnt != 128:
            print(amnt, '/' , total , '=' , amnt/total, ' *' ,  (total-amnt) / (amnt/(t.time()-func_start))/60 , 'm'  )
    #print(all)
    dbg('%check_vars')
    return all

from multiprocessing import Pool

#check_vars({'time_0':(1,2,3), 'samples':(6,7,8)} , 10, 100, 20)

if __name__ == '__main__':
    
    catch_points = []
    catch_dict = {}

    with open('dbg\\catches.txt', 'r') as ff:
        dat = ff.read()
        points = []
        for s in dat.split('\n'):
            if len(s):
                obj = json.loads(s)
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
                snap_points.append(obj[1])
                snap_dict[obj[0]] = obj[1]
                
                #if len(snap_points) > 2:
                    #print('snap_pppp', snap_points[0][2])
                    #snap_lengths.append( ( snap_points[-1], abs( snap_points[-1][0][1] - snap_points[-1][-1][1] ) ))
                #break
                #if len(snap_points) > 6:
                #    break

    print('SNAPS',len(snap_points), 'CATCHES', len(catch_points))
    if 1:
        minf = 28, 56, 1
        all_variable_vars = ['overshootp', 'min_trigger_val', 'max_large_freq', 'time_m', 'time_0', 'xy_ratio', 'freq_intensities']
        fixed_vars = {
            #'freq_intensities':[
            #    [1.3,1,0.6,0],
            #],
        }
        iter_size = 0.06
        best_var = DEF_VAR
        best_score = 99
        while True:
            var_lists_low = {}
            var_lists_high = {}
            variable_vars = all_variable_vars[:]
            for o in range(3):
                ro = rnd.randint(0, len(variable_vars) -1)
                if variable_vars[ro] == 'freq_intensities':
                    ro = rnd.randint(0, len(variable_vars) -1)
                print(', reusing ', variable_vars[ro],end='')
                var_lists_low[variable_vars[ro]] = (best_var[variable_vars[ro]], )
                var_lists_high[variable_vars[ro]] = (best_var[variable_vars[ro]], )
                del variable_vars[ ro ]
            for variable_var in variable_vars:
                rand = rnd.uniform(0.05, 1.0)
                print(', modding', variable_var, ' +- ', rand * iter_size, end='')
                if variable_var == 'freq_intensities':
                    
                    index = rnd.randint(0,len(best_var[variable_var])-1)
                    best_val = best_var[variable_var][index]
                    
                    new_low = best_val + DEF_VAR[variable_var][index] * iter_size * rand
                    new_high = best_val - DEF_VAR[variable_var][index] * iter_size * rand
                    
                    new_list_low = best_var[variable_var][:]
                    new_list_high = best_var[variable_var][:]
                    
                    new_list_low[index] = new_low
                    new_list_high[index] = new_high
                    
                    var_lists_low[variable_var] = [new_list_low]
                    var_lists_high[variable_var] = [new_list_low]

                else:
                    var_lists_low[variable_var] = (best_var[variable_var], best_var[variable_var] + DEF_VAR[variable_var] * iter_size * rand)
                    var_lists_high[variable_var] = (best_var[variable_var], best_var[variable_var] - DEF_VAR[variable_var] * iter_size * rand)
            for fixed_var_key, fixed_var_value in fixed_vars.items():
                print(', using fixed', fixed_var_key, end = '')
                var_lists_low[fixed_var_key] = fixed_var_value
                var_lists_high[fixed_var_key] = fixed_var_value
            print('')
            def p(v):
                print('making', v)
                return (v, *minf, snap_points, catch_points)

            inps = (p(var_lists_low), p(var_lists_high))

            print('start procs')
            with Pool(2) as p:
                res = p.map(check_vars, inps)
            
            all = []
            for r in res:
                all += r
            #print(all)

            all.sort(key=( lambda x: x['snap_ratio'] + 0.2 * x['catch_ratio'] ))
            new_best = all[0]
            new_score = new_best['snap_ratio'] + 0.2 * new_best['catch_ratio']
            print('\n========GOT BEST', all[0:3])
            if new_score < best_score:
                print('using ^^^')
                best_score = new_score
                best_var = new_best['var']
                with open('dbg/simtests.txt', 'a+') as file:
                    file.write(json.dumps( {'run':'a111', 'data':new_best} ) + '\n')
            
        
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
        
        minf = 28, 56, 2

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
    window = pygame.display.set_mode( WINDOW_SIZE )
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
