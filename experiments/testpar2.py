from multiprocessing import Pool
import matplotlib.pyplot as plt
import random as r
import json
from scipy.stats import linregress
from PIL import Image
import sys

AVERAGEMIN = 1
AVERAGEMAX = 3
DISTMIN = 22
DISTMAX = 40
HITMIN = 9
HITMAX = 19

print('tota;', (AVERAGEMAX-AVERAGEMIN) * (DISTMAX-DISTMIN) * (HITMAX-HITMIN) // 6
    )

PULLING_TL = 1940-39, 840-15
PULLING_BR = 2000-30, 900-15
PULLING_SCAN_SPEED = 7
    
SCANX = PULLING_TL[0]-100
SCANY = PULLING_TL[1]-100
SZX = PULLING_BR[0]+100 - SCANX
SZY = PULLING_BR[1]+100 - SCANY

def dist (p1, p2):
    return sum([ (p1[i] - p2[i])**2 for i in range(2)]) ** 0.5

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

def scrn2canv(pos):
    return max(pos[0] - SCANX, 0), max(min(pos[1] - SCANY-1, SZY),0)

class FishTest:
    def __init__(self, data, dangers, average, maxdist, maxhit, shouldpass, endtime=4.1, showim = False):
        self.data = data
        self.iters = 0##
        self.dangers = dangers
        self.maxdist = maxdist
        self.average = average

        self.maxhit = maxhit
        self.hits = 0
        self.passed = None
        self.shouldpass = shouldpass
        self.showim = showim
        self.endtime = endtime
        self.im = None
        
    def fish(self):
        end_unix = get_end_time_session(self.data) - self.endtime
        if self.showim:
            self.im = Image.new("RGB", (SZX, SZY))
            for danger in dangers:
                self.im.putpixel(scrn2canv(danger), (255,0,0))

        for iterdata in self.data[::-1]:
            pos = get_pos_iter(iterdata)
            if end_unix < pos[2]:
                self.passed = False
                break
            if danger_zone(self.dangers, pos, self.maxdist):
                self.hits += 1
                if self.im:
                    self.im.putpixel(scrn2canv(pos), (0,255,0)  )
                if self.hits >= self.maxhit:
                    self.passed = True
                    break
            elif self.im:
                self.im.putpixel(scrn2canv(pos), (0,255,255)  )
        else:
            self.passed = False
        if self.im:
            self.im.show()
        return self.passed

def check(catchseshs, snapseshs, dangers, averagei, disti, maxhiti):
    catch_pass = 0
    catch_fail = 0
    for catchsesh in catchseshs:
        ft = FishTest(catchsesh, dangers, averagei, disti, maxhiti, False, 0)
        ft.fish()
        if ft.passed == ft.shouldpass:
            catch_pass += 1
        else:
            catch_fail += 1

    snap_pass = 0
    snap_fail = 0
    for snapsesh in snapseshs:
        ft = FishTest(snapsesh, dangers, averagei, disti, maxhiti, True, 4.1)
        ft.fish()
        if ft.passed == ft.shouldpass:
            snap_pass += 1
        else:
            snap_fail += 1
    print('avg',averagei,'dist',disti,'maxhit',maxhiti,' res==',catch_fail/ max(1, catch_pass), snap_fail / max(1, snap_pass))
    return (snap_fail / max(1, snap_pass), catch_fail/ max(1, catch_pass))


def f2(params):
    catch_points, snap_points, dangers, catch_mult = params
    scores = []
    iis = 0
    total = (AVERAGEMAX-AVERAGEMIN) * (DISTMAX-DISTMIN) * (HITMAX-HITMIN) // 6
    for averagei in range(AVERAGEMIN, AVERAGEMAX):
        for disti in range(DISTMIN, DISTMAX,3):
            for maxhiti in range(HITMIN, HITMAX,2):
                vals = check(catch_points, snap_points,dangers, averagei, disti, maxhiti)
                score = vals[0] + vals[1] * catch_mult
                scores.append([ (averagei, disti, maxhiti, vals[0]), score ])
                scores.sort(key=(lambda x: x[1]))
                scores = scores[:4]
                print(iis,'/', total)

                iis += 1
                #sys.stdout.flush()
                
    return scores

def f(x):
    return x*x

if __name__ == '__main__':
    print('prepping')
    catch_points = []
    with open('..\dbg\\catches.txt', 'r') as ff:
        dat = ff.read()
        for s in dat.split('\n'):
            if len(s):
                catch_points.append(json.loads(s))
                if len(catch_points) > 10:
                    break
                

    snap_points = []

    with open('..\dbg\\snaps.txt', 'r') as ff:
        dat = ff.read()
        points = []
        for s in dat.split('\n'):
            if len(s):
                snap_points.append(json.loads(s))
                #break
                if len(snap_points) > 10:
                    break
                

    dangers = []
    dangerim = Image.open(r'C:\Users\Monchy\Documents\RustFishingBot\rust\dangermap.png')
    for x in range(dangerim.size[0]):
        for y in range(dangerim.size[1]):

            px = dangerim.getpixel((x,y))
            if px[2] > 10:
                dangers.append((x+SCANX,y+SCANY))
                #break
    dangerim = None

    catch_points = catch_points
    snap_points = snap_points
    

    ft = FishTest(catch_points[7], dangers, 1, 2, 11, True, 4.1, showim=True)
    ft.fish()

    raise Exception('stop')
    print('spawning')
    inps = []
    for mult in (0.2,0.15,0.1):
        inps.append((snap_points, catch_points, dangers, mult))
    with Pool(3) as p:
        res = p.map(f2, inps)
        
