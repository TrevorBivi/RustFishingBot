import matplotlib.pyplot as plt

import json

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

catch_points = []
with open('dbg\\catches.txt', 'r') as f:
    dat = f.read()
    for s in dat.split('\n'):
        if len(s):
            catch_points.append(json.loads(s))

snap_points = []
with open('dbg\\snaps.txt', 'r') as f:
        dat = f.read()
        points = []
        for s in dat.split('\n'):
            if len(s):
                snap_points.append(json.loads(s))


def plotfig(fff, samples_min, samples_max, name = None , itera = 2):
    if name == None:
        name = str(t.time())[7:14] + '_'

    print('plotting', name)

    sz = '.'
    for samples in range(samples_min, samples_max, itera):
        plt.clf()
        for i in range(100):
        
            for pl in catch_points:
                if i < len(pl) and i < 60:
                    x = pl[0][2] - pl[i][2]
                    y = fff([  lli for lli in pl[i:min(i+samples, len(pl))] ])
                    plt.plot(x, y, sz , color='blue')
            for pl in snap_points:
                if i < len(pl) and pl[0][2] > pl[i][2] + 3:
                    #print(ls[0], ls[i])
                    x = pl[0][2] - pl[i][2] - 4.1
                    y = fff([  lli for lli in pl[i:min(i+samples, len(pl))] ])
                    plt.plot(x, y, sz, color='red')

        plt.savefig('plots\\' + name + '_' + str(samples) + '.png')
            
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
'''
plotfig( lambda ll : ar(ll), 4, 20, 'ar(pos) s-')
plotfig( lambda ll : ar(der(ll)), 4, 20, 'ar(vel) s-')
plotfig( lambda ll : ar(der(der(ll))), 4, 20, 'ar(acc) s-')
