import matplotlib.pyplot as plt
import random as r
import json
from scipy.stats import linregress
from PIL import Image

def dist (p1, p2):
    return sum([ (p1[i] - p2[i])**2 for i in range(2)]) ** 0.5

def sse(ll):
    if len(ll) < 2:
        return 0
    avg = sum([l[0] for l in ll])/len(ll)
    avgy = sum([l[1] for l in ll])/len(ll)
    return sum([ (abs(xi[0] - avg)**2  + abs(xi[1] - avgy)**2)   for xi in ll])

def abse(ll):
    if len(ll) < 2:
        return 0
    avg = sum([l[0] for l in ll])/len(ll)
    avgy = sum([l[1] for l in ll])/len(ll)
    return sum([ (abs(xi[0] - avg) + abs(xi[1] - avgy))   for xi in ll])

def ar(ll):
    if len(ll) == 0:
        return 0
    minx = 99999
    maxx = -9999
    
    miny = 99999
    maxy = -9999

    for l in ll:
        minx = min(minx, l[0])
        maxx = max(maxx, l[0])
        miny = min(miny, l[1])
        maxy = max(maxy, l[1])
    return (maxx-minx) * (maxy-miny)
'''
def art2(ll):
    if len(ll) < 2:
        return 0
    minx = 99999
    maxx = -9999
    
    miny = 99999
    maxy = -9999

    minx2 = 99999
    maxx2 = -9999
    
    miny2 = 99999
    maxy2 = -9999

    for l in ll:
        if l[0] < minx2:
            if l[0] < minx:
                minx2 = 
            minx2 = l[0]
            minx = minx2
        if l[0] > maxx2:
            maxx2 = l[0]
            maxx = maxx2
'
    return (maxx-minx) * (maxy-miny)'''

def der(ll):
    new = []
    #print(ll)
    for i in range(0, len(ll)-1):
        
        new_dt = ll[i][2] - ll[i+1][2]
        if new_dt == 0.0:
            new_x = 0
            new_y = 0
        #new_x = ll[i][0] - ll[i+1][0]/new_dt
        #new_y = ll[i][1] - ll[i+1][1]/new_dt
        else:
            new_x = (ll[i][0] - ll[i+1][0])/new_dt
            new_y = (ll[i][1] - ll[i+1][1])/new_dt
        new.append((new_x, new_y, ll[i][2]))
    return new

def ldist(ll):
    d = 0
    for i in range(0, len(ll)-1):
        d += dist(ll[i], ll[i+1])
    return d

def lrootdist(ll):
    d = 0
    for i in range(0, len(ll)-1):
        d += dist(ll[i], ll[i+1]) ** 0.5
    return d

def acc(ll):
    if len( ll) < 3:
        return 0
    last_dt = ll[0][2] - ll[1][2]
    if last_dt == 0:
        return -1
    last_vx = (ll[0][0] - ll[1][0]) / last_dt
    last_vy = (ll[0][1] - ll[1][1]) / last_dt

    vxs = []
    vys = []
    acc = 0
    for i in range(2, len(ll)):
        new = ll[i-1]
        old = ll[i]
        new_dt = old[2] - new[2]
        if new_dt == 0:
            return -1
        new_vx = (old[0] - new[0])/new_dt
        new_vy = (old[1] - new[1])/new_dt

        acc += dist((last_vx, last_vy),(new_vx, new_vy))
        last_vx = new_vx
        last_vy = new_vy
        

    return acc

def trav(ll):
    ret = 0
    last_x = ll[0][0]
    last_y = ll[0][1]
    

    
    for i in range(1,len(ll)):
        ret += dist( (last_x, last_y), (ll[i][0], ll[i][1]))
        last_x = ll[i][0]
        last_y = ll[i][1]
    return ret

def a(ll):
    return ldist(der(der(ll)))#ldist(der(der(ll)))#sse(der(der(ll)))#ldist(der(der(ll)))

def area(ll):
    minx = min([l[0] for l in ll])
    maxx = max([l[0] for l in ll])
    return maxx-minx
    

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


def linr(ll):
    if len(ll) < 4:
        return 0
    xs = []
    ys = []
    for p in ll:
        xs.append(p[0])
        ys.append(p[1])
    #print(ll)
    #print(';;')
    # print(xs)
    # print('pp')
    # print(ys)
    res = linregress(xs,ys)
    return abs(res.rvalue)

def linr_i(ll, i):
    vs = []
    ts = []
    for p in ll:
        vs.append(p[i])
        ts.append(p[2])
    res = linregress(vs,ts)
    return abs(res.rvalue)

def sse_i(ll,i):
    if len(ll) < 2:
        return 0
    avg = sum([l[i] for l in ll])/len(ll)
    return sum([ (xi[i] - avg)**2 for xi in ll])
    
def sse_r(ll, scale_y = 1):
    return sse(ll) * (1-linr(ll))

def sse_r2(ll, scale_y = 1):
    return sse_i(ll,0) * (1-linr_i(ll,0)) + (sse_i(ll,1) * (1-linr_i(ll,1))) * scale_y


def plotfig(fff, samples_min, samples_max, name = None , itera = 2):
    if name == None:
        name = str(t.time())[7:14] + '_'

    print('plotting', name)

    sz = ','
    for samples in range(samples_min, samples_max, itera):
        plt.clf()
        print('doing ', samples)
        for i in range(160):


            #catch_points[0][0][0] [sample][iter][0 ? posss  1 - time] 
            
            for pl in catch_points:
                if i < len(pl) and i < 60:

                    #d(time) == catch_time - snap_time
                    x = pl[i][1] - pl[0][1]
                    y = fff(pl[i][0][:samples]) #get time index i of samples
                    plt.plot(x, y, sz , color='blue')
            for pl in snap_points:
                
                #print('snap len', pl[0][1] - pl[-1][2])
                if i < len(pl):
                    #print(ls[0], ls[i])
                    x = pl[i][1] - (pl[0][1] - 4.1)
                    if x < 0.5:
                        y = fff(pl[i][0][:samples])
                        plt.plot(x, y, sz, color='red')

        plt.savefig('..\\plots\\' + name + '_' + str(samples) + '.png')



class snap_detector:
    def __init__(self, ll, func, samples, should_pass, max_passing = 20):
        self.ll = ll
        self.func = func
        self.should_pass = should_pass
        self.samples= samples
        self.loop = 0
        self.loops_passing = 0
        self.max_passing = 20
        self.passes = False
        
    def check(self):
        for i in range(len(self.ll)):
            if self.func(self.ll[-1-i][0]):
                self.loops_passing += 1
            #print(  self.max_passing, self.loops_passing, self.max_passing <= self.loops_passing)
            if self.max_passing <= self.loops_passing:
                self.passes = True
                break

bad_points = []
for pl in catch_points:
    #all lists of position lists
    for p in pl:
       
        #print('in' ,p[0][-1])
        bad_points.append(
            (
                round(p[0][-1][0]),
                round(p[0][-1][1])
                )
        )

check_points = []
for pl in snap_points:
    for p in pl:
        #if time less that end time - 4
        #print('time check ', p[1], pl[0][1])
        if p[1] < pl[0][1]-4:
            check_points.append(( round(p[0][-1][0]), round(p[0][-1][1])))
'''
good_points = []
mindist = 3
for i,cp in enumerate(check_points):
    print(i,'/',len(check_points))
    for bp in bad_points:
        if dist(cp,bp) < mindist:
            break
    else:
        good_points.append(cp)'''
PULLING_TL = 1940-39, 840-15
PULLING_BR = 2000-30, 900-15
PULLING_SCAN_SPEED = 7
    
SCANX = PULLING_TL[0]-100
SCANY = PULLING_TL[1]-100
SZX = PULLING_BR[0]+100 - SCANX
SZY = PULLING_BR[1]+100 - SCANY

def show_points(points, col, ii):
    global SCANX, SCANY, SZX, SZY
    errs = 0
    
    for i,gp in enumerate(points):
        pos = (round(gp[0] - SCANX), round(gp[1] - SCANY))
        if i % 1000 == 0:
            print(i, len(points))
        if 0 <= pos[0] < SZX and 0 <= pos[1] < SZY:
            try:
                cur_col = ii.getpixel(pos)
                new_col = cur_col[0] //2 + col[0] //2, cur_col[1] //2 + col[1] //2, cur_col[2] //2 + col[2] //2
                ii.putpixel( pos , new_col)
            except IndexError:
                print('wtf', SZX, SZY, ii.size, pos)
        else:
            errs += 1
            #print('err',errs,i ,'--', pos, gp, '--', gp)
'''
ii = Image.new('RGB', (SZX, SZY))

sps = []
for cp in check_points:
    closes = 4
    for bp in bad_points:
        if dist(bp,cp) < 4:
            closes -= 1
            if closes == 0:
                break
    else:
        sps.append(cp)
print('show bad')


show_points(sps, (0,0,255), ii)'''
#print('show good')
#show_points(check_points, (255,0,0), ii)

#raise Exception('STOP')




#plotfig( lambda ll : sse_r(ll), 4, 28, 'sse_r(pos) s-')
#plotfig( lambda ll : sse_r(der(ll)), 8, 28, 'sse_r(vel) s-')

dangers = []
dangerim = Image.open(r'C:\Users\Monchy\Documents\RustFishingBot\rust\dangermap.png')
for x in range(dangerim.size[0]):
    for y in range(dangerim.size[1]):
        px = dangerim.getpixel((x,y))
        if px[2] > 10:
            dangers.append((x+SCANX,y+SCANY))
                
def danger_zone(ll, mdist = 3):
    pos = ll[0]
    #print(pos)
    for d in dangers:
        if dist(pos[:2], d[:2]) <= mdist:
            return True
    return False

datas = []
for acc_ratio in (1, 0.8, 0.6, 0.4, 0.2):
    best = 999999999
    chosen = None


    for scale_y in [1]:#(0.7, 0.9, 1, 1.1, 1.3):
        for max_passing in range(2, 25, 2):
            for min_err in [False]:# range(500000, 1300000, 50000):
                for calc_passes in [1]:# range(14,24,3):
                    test = {'accratio': acc_ratio, 'scale_y': scale_y, 'max_passing': max_passing, 'minerr': min_err, 'calc passes': calc_passes}
                    
                    fails = 0
                    passess = 0
                    for pl in catch_points:
                        def passesf(ll):
                            #print('compare' ,sse_r(der(ll)) , min_err)
                            #print('vv',ldist(der(ll)))
                            return danger_zone(ll) > min_err
                        
                        sd = snap_detector(pl, passesf, calc_passes, False, max_passing)
                        sd.check()
                        if sd.passes == sd.should_pass:
                            passess += 1
                        else:
                            fails += 1
                    snap_fails = 0
                    snap_passes = 0
                    for i,pl in enumerate(snap_points):
                        def passesf(ll):
                            try:
                                if len(ll) == 0 or len(pl) == 0 or pl[0][2] - ll[0][2] < 4.1:
                                    return False
                                #print('vv',ldist(der(ll)))
                                return danger_zone(ll) > min_err
                            except IndexError:
                                print('ll',ll)
                                print('pli',i)
                                raise IndexError()
                        
                        sd = snap_detector(pl, passesf, calc_passes, True, max_passing)
                        sd.check()
                        if sd.passes == sd.should_pass:
                            passess += 1
                            snap_passes += 1
                        else:
                            fails += 1
                            snap_fails += 1
                    
                    ratio = snap_fails / max(1, snap_passes) + fails/max(1, passess) * acc_ratio
                    print('tested ',test,'\n total', fails, passess, 'snap', snap_passes, snap_fails, 'ratio', ratio)
                    
                    if ratio < best:
                        best = ratio
                        chosen = {'accratio': acc_ratio, 'scale_y': scale_y, 'max_passing': max_passing, 'minerr': min_err, 'calc passes': calc_passes}
    value = (snap_fails/max(1, snap_passes), fails/max(1,passess), best, chosen)
    datas.append( value )                    
    print(datas)
import pygame
from math import *
import math as m
from basicHelpers import *
#from persp_proj_tests import *

WINDOW_SIZE =  800
ROTATE_SPEED = 3.141592 * 0.01
window = pygame.display.set_mode( (2560//2, 1440//2) )
clock = pygame.time.Clock()


ll = []
while True:
    clock.tick(60)
    window.fill((0,0,0))
    if len(ll):
        pos = ll.pop(-1)
        print('draw',pos)
        pygame.draw.circle(window, (0,0,255), (pos[0]-1700, pos[1]-600) , 2)
    pygame.display.update()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            ll = snap_points[r.randint(0,len(snap_points)-1)][:]
        elif keys[pygame.K_a]:
            ll = catch_points[r.randint(0,len(catch_points)-1)][:]
        
        else:
            continue
        
        #print(angle_x, angle_y, angle_z)
        
    
#im = 


#plotfig( lambda ll : lrootdist(der(der(ll))), 4, 25, 'rootldist(acc) s-')
#plotfig( lambda ll : abse(ll), 4, 25, 'abse(pos) s-')
#plotfig( lambda ll : area(ll), 4, 25, 'x width s-')
'''
plotfig( lambda ll : ldist(ll), 4, 20, 'ldist(pos) s-')
plotfig( lambda ll : sse(ll), 4, 20, 'sse(pos) s-')
plotfig( lambda ll : abse(ll), 4, 20, 'abse(pos) s-')
    
plotfig( lambda ll : ldist(der(ll)), 4, 20, 'ldist(vel) s-')
plotfig( lambda ll : sse(der(ll)), 4, 20, 'sse(vel) s-')
plotfig( lambda ll : abse(der(ll)), 4, 20, 'abse(pos) s-' )
    
plotfig( lambda ll : ldist(der(der(ll))), 4, 20, 'ldist(acc) s-')
plotfig( lambda ll : sse(der(der(ll))), 4, 20, 'sse(acc) s-')
plotfig( lambda ll : abse(der(der(ll))), 4, 20, 'abse(pos) s-')
             
plotfig( lambda ll : ldist(der(der(der(ll)))), 4, 20, 'ldist(acc2) s-')
plotfig( lambda ll : sse(der(der(der(ll)))), 4, 20, 'sse(acc2) s-' )
plotfig( lambda ll : abse(der(der(der(ll)))), 4, 20, 'abse(pos) s-')

plotfig( lambda ll : ar(ll), 4, 20, 'ar(pos) s-')
plotfig( lambda ll : ar(der(ll)), 4, 20, 'ar(vel) s-')
plotfig( lambda ll : ar(der(der(ll))), 4, 20, 'ar(acc) s-')
'''
