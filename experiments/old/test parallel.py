from multiprocessing import Pool
import matplotlib.pyplot as plt
import random as r
import json
from scipy.stats import linregress
from PIL import Image

AVERAGEMIN = 1
AVERAGEMAX = 2
DISTMIN = 1
DISTMAX = 30
HITMIN = 1
HITMAX = 20

PULLING_TL = 1940-39, 840-15
PULLING_BR = 2000-30, 900-15
PULLING_SCAN_SPEED = 7
    
SCANX = PULLING_TL[0]-100
SCANY = PULLING_TL[1]-100
SZX = PULLING_BR[0]+100 - SCANX
SZY = PULLING_BR[1]+100 - SCANY

def get_pos_outcome(outcome, session, itern, average = 1):

    x = 0
    y = 0
    for i in average:
        x += outcome[session][itern][0][-1 - i][0]
        y += outcome[session][itern][0][-1 - i][1]
    x /= average
    y /= average
    return round(x), round(y), outcome[session][itern][0][-1 - i][2]

def get_pos_iter(itern, average = 1):

    x = 0
    y = 0
    for i in range(average):
        x += itern[0][-1 - i][0]
        y += itern[0][-1 - i][1]
    x /= average
    y /= average
    return round(x), round(y), itern[0][-1 - i][2]

def get_end_time_session(session):
    return session[0][0][-1][2]

def danger_zone(dangers, pos, mdist = 3):
    for d in dangers:
        if dist(pos[:2], d[:2]) <= mdist:
            return True
    return False

class FishTest:
    def __init__(self, data, dangers, maxhit, maxdist, average, shouldpass, endtime=4.1):
        self.data = data
        self.iters = 0##
        self.dangers = dangers
        self.maxdist = maxdist
        self.average = average

        self.maxhit = maxhit
        self.hits = 0
        self.passed = None
        self.shouldpass = shouldpass
        
        self.endtime = endtime

        
    def fish(self):
        end_unix = get_end_time_session(self.data) - self.endtime
        
        for iterdata in self.data[::-1]:
            pos = get_pos_iter(iterdata)
            if end_unix < pos[2]:
                self.passed = False
                break
            if danger_zone(self.dangers, pos, self.maxdist):
                self.hits += 1
                if self.hits >= self.maxhit:
                    self.passed = True
                    break
        else:
            self.passed = False
        return self.passed
    




def check(catchseshs, snapseshs, dangers, averagei, disti, maxhiti):
    catch_pass = 0
    catch_fail = 0
    for catchsesh in catchseshs:
        ft = FishTest(catchsesh, dangers, maxhiti, disti, averagei, False, 0)
        ft.fish()
        if ft.passed == ft.shouldpass:
            catch_pass += 1
        else:
            catch_fail += 1

    snap_pass = 0
    snap_fail = 0
    for snapsesh in snapseshs:
        ft = FishTest(snapsesh,dangers, maxhiti, disti, averagei, True, 4.1)
        ft.fish()
        if ft.passed == ft.shouldpass:
            snap_pass += 1
        else:
            snap_fail += 1
    print('avg',averagei,'dist',disti,'maxhit',maxhiti,' res==',catch_fail/ max(1, catch_pass), snap_fail / max(1, snap_pass))
    return (snap_fail / max(1, snap_pass), catch_fail/ max(1, catch_pass))

def f(params):
    catch_points, snap_points, dangers, catch_mult = params
    scores = []
    
    for averagei in range(AVERAGEMIN, AVERAGEMAX):
        for disti in range(DISTMIN, DISTMAX):
            for maxhiti in range(HITMIN, HITMAX):
                vals = check(catch_points, snap_points, averagei, disti, maxhiti)
                score = vals[0] + vals[1] * catch_mul
                scores.append([ (averagei, disti, maxhiti), score ])
                scores.sort(key=(lambda x: x[1]))
                scores = scores[:4]
    return scores

PROC = 5            
if __name__ == '__main__':
        
    print('prepping')
    catch_points = []
    with open('..\dbg\\catches.txt', 'r') as f:
        dat = f.read()
        for s in dat.split('\n'):
            break
            if len(s):
                catch_points.append(json.loads(s))
                

    snap_points = []

    with open('..\dbg\\snaps.txt', 'r') as f:
        dat = f.read()
        points = []
        for s in dat.split('\n'):
            break
            if len(s):
                snap_points.append(json.loads(s))
                

    dangers = []
    dangerim = Image.open(r'C:\Users\Monchy\Documents\RustFishingBot\rust\dangermap.png')
    for x in range(dangerim.size[0]):
        for y in range(dangerim.size[1]):
            break
            px = dangerim.getpixel((x,y))
            if px[2] > 10:
                dangers.append((x+SCANX,y+SCANY))
                
            
    print('spawning')
    inps = []
    done = None
    for mult in (1, 0.8, 0.6, 0.4, 0.2):
        inps.append( 1)#[ catch_points[:2], snap_points[:2], dangers[:2], mult])
    with Pool(5) as p:
        done = p.map(f, inps)
        print('DONE1')
    print('DONE2')
