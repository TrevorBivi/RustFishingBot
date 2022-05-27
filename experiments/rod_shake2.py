import matplotlib.pyplot as plt
import random as r
import json
from scipy.stats import linregress
from PIL import Image

def dist (p1, p2):
    return sum([ (p1[i] - p2[i])**2 for i in range(2)]) ** 0.5


PULLING_TL = 1940-39, 840-15
PULLING_BR = 2000-30, 900-15
PULLING_SCAN_SPEED = 7
    
SCANX = PULLING_TL[0]-100
SCANY = PULLING_TL[1]-100
SZX = PULLING_BR[0]+100 - SCANX
SZY = PULLING_BR[1]+100 - SCANY

catch_points = []
with open('..\dbg\\catches.txt', 'r') as f:
    dat = f.read()
    for s in dat.split('\n'):
        if len(s):
            catch_points.append(json.loads(s))

snap_points = []

with open('..\dbg\\snaps.txt', 'r') as f:
        dat = f.read()
        points = []
        for s in dat.split('\n'):
            if len(s):
                snap_points.append(json.loads(s))

dangers = []
dangerim = Image.open(r'C:\Users\Monchy\Documents\RustFishingBot\rust\dangermap.png')
for x in range(dangerim.size[0]):
    for y in range(dangerim.size[1]):
        px = dangerim.getpixel((x,y))
        if px[2] > 10:
            dangers.append((x+SCANX,y+SCANY))
                
def danger_zone(pos, mdist = 3):
    for d in dangers:
        if dist(pos[:2], d[:2]) <= mdist:
            return True
    return False


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

class FishTest:
    def __init__(self, data, maxhit, maxdist, average, shouldpass, endtime=4.1):
        self.data = data
        self.iters = 0##

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
            if danger_zone(pos, self.maxdist):
                self.hits += 1
                if self.hits >= self.maxhit:
                    self.passed = True
                    break
        else:
            self.passed = False
        return self.passed


def check(averagei, disti, maxhiti):
    catch_pass = 0
    catch_fail = 0
    for catchsesh in catch_points:
        ft = FishTest(catchsesh, maxhiti, disti, averagei, False, 0)
        ft.fish()
        if ft.passed == ft.shouldpass:
            catch_pass += 1
        else:
            catch_fail += 1

    snap_pass = 0
    snap_fail = 0
    for snapsesh in snap_points:
        ft = FishTest(snapsesh, maxhiti, disti, averagei, False, 0)
        ft.fish()
        if ft.passed == ft.shouldpass:
            snap_pass += 1
        else:
            snap_fail += 1
    print('avg',averagei,'dist',disti,'maxhit',maxhiti,' res==',catch_fail/ max(1, catch_pass), snap_fail / max(1, snap_pass))


for averagei in range(1,3):
    for disti in range(2, 15,2):
        for maxhiti in range(1,10):
            check(averagei, disti, maxhiti)
