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
from math import *
from pygame.locals import *
import math as m
#from basicHelpers import *
#from persp_proj_tests import *



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

class Fisht:
    def __init__(self, sesh, passval, timescore = 0, bin2score = 1, overshootp=1):
        self.sesh = sesh
        self.passval = passval
        self.passes = 0
        self.time = 0
        self.timescore = timescore
        self.bin2score = bin2score
        self.overshootp = overshootp
        self.timescores = []
    def score(self):
        pass

    def fish(self):
        for iter in self.sesh:
            self.time = iter[-1][2] - self.sesh[0][0][2]
            timeval = self.timescore * (self.time-2.8)
            if len(iter) < 40:
                continue
            val = timeval + fft_snap(iter)[2][2]  + fft_snap(iter)[2][3] * self.bin2score 
            if val >= self.passval:
                self.passes += self.passval + (val - self.passval) * self.overshootp
            self.timescores.append((self.time,self.passes))

#x = np.linspace(0.0, N*T, N, endpoint=False)
#y = np.sin(50.0 * 2.0*np.pi*x) + 0.5*np.sin(80.0 * 2.0*np.pi*x)
#yf = fft(y)
#xf = fftfreq(N, T)[:N//2]
#plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
#plt.grid()
#plt.show()



catch_points = []


with open('dbg\\catches.txt', 'r') as ff:
    dat = ff.read()
    points = []
    for s in dat.split('\n'):
        if len(s):
            obj = json.loads(s)
            catch_points.append(obj[1])
            
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
    for s in dat.split('\n'):
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

def cut(sesh, amnt):
    end_time = sesh[-1][-1][2]
    poss = []
    for pos in sesh:
        if end_time - pos[-1][2] < amnt:
            break
        poss.append(pos)
    return poss

all = []
if 1:
    for overshootp in (0,0.5,1):
        for bin2score in (0,1.5,3):
            #if overshootp == bin2score:
            #    continue
            for max_val in range(480,1100,80):
                for time_val in range(25, 50, 6):
                    fshs = []
                    sfshs = []
                    for cp in catch_points:
                        #print('doing')
                        cp = cut(cp, 0.8)
                        fsh = Fisht(cp, max_val, time_val, bin2score, overshootp)
                        fsh.fish()
                        fshs.append(fsh)
                    for sp in snap_points:
                        sp = cut(sp, 4.3)
                        fsh = Fisht(sp, max_val, time_val, bin2score, overshootp)
                        fsh.fish()
                        sfshs.append(fsh)

                    for max_pass in range(28*max_val,50*max_val,2*max_val):
                        snap = 0
                        fine = 0
                        times = []
                        #nsnap = []
                        #nfine = []
                        for i, fsh in enumerate(fshs):
                            if fsh.passes >= max_pass: # BAD
                                snap += 1
                                for ts in fsh.timescores:
                                    if ts[1] >= max_pass:
                                        times.append(ts[0])
                                #nsnap.append(i)
                            else: #GOOD
                                fine += 1
                                #nfine.append(i)
                        
                        ssnap = 0
                        sfine = 0

                        nssnap = []
                        #nsfine = []
                        stimes = []
                        for i, fsh in enumerate(sfshs):
                            if fsh.passes < max_pass: #BAX
                                ssnap += 1
                                nssnap.append(i)
                            else: #GOOD
                                for ts in fsh.timescores:
                                    if ts[1] >= max_pass:
                                        stimes.append(ts[0])
                                        break
                                sfine += 1
                                #nsfine.append(i)
                        print('lens', len(times), len(stimes))
                        avtm = sum(times)/max(1,len(times))
                        avstm = sum(stimes)/max(1,len(stimes))
                        obj={
                            'ovsht': overshootp,
                            'bin2sc': bin2score,
                            'max':max_val,
                            'timeval':time_val,
                            'pass':max_pass,
                            'ssnap':ssnap,
                            'sfine':sfine,
                            'sratio':ssnap/max(1,sfine),
                            'avst':avstm,
                            'snap':snap,
                            
                            'fine':fine,
                            'ratio': snap/max(1, fine),
                            'avt':avtm,
                            #'ssnapis': nsnap,
                            #'sfineis': nfine,
                            'nsnapis': nssnap,
                            #'nfineis': nsfine
                        }
                        all.append(obj)
                        '''with open('test1.txt', 'w+') as f1:
                            f1.write(json.dumps(all))
                        with open('test2.txt', 'w+') as f2:
                            f2.write(json.dumps(all))'''
                        
                        print(obj)

    for safemult in (0.1, 0.15, 0.2, 0.4):
        all.sort(key=(lambda x: x['sratio'] + x['ratio'] * safemult  ))

        print(safemult,'==========BEST')
        for aa in all[:4]:
            print(aa)

            #print(all)

    raise Exception('stop')
    #snap_lengths.sort(key = (lambda x: x[1]))
    #print('snap_lengths', snap_lengths[:5], snap_lengths[-5:])


print('lefisher',len(snap_points))
seshname = "726.7"

sesh = snap_dict[seshname]
prefixed = [filename for filename in os.listdir('E:\\tempvideo\\fisher\\') if filename.startswith(seshname)]
print(prefixed)
end_time = sesh[-1][-1][2] - sesh[0][0][2] - 4.1
print(end_time)






WINDOW_SIZE =  600, 800
SPEED = 0.025
window = pygame.display.set_mode( WINDOW_SIZE )
clock = pygame.time.Clock()
new = True
while True:

    clock.tick(6)
    if new:
        new = False
        window.fill((0,0,0))
        im = None
        chosen = None
        for i, snap in enumerate(sesh):
            if end_time <= snap[-1][2] - sesh[0][0][2]:
                im = Image.open('E:\\tempvideo\\fisher\\' + prefixed[i])
                chosen = snap[-40:]
                break

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
        xf, yf, sf, fa= fft_snap( chosen , True)
        fig = plt.figure()
        N = len(chosen)
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(fa[:N//2], yf[:N//2])
        ax.plot(fa[:N//2], xf[:N//2])
        #ax.plot( fa[2], abs(sf)[2] )
        
        print(abs(sf[:]))
        ax.plot(fa[:N//2], sf[:N//2])
        ax.plot([0,0.3], [ sf[2],  sf[2]])

        time_str = chosen[-1][2] - sesh[0][-1][2]
        ax.set_ylim([0,800])
        #ax.set_xlim([-0.2,0.2])
        ax.set_title(str(time_str) + '  smp ' + str(len(chosen)))
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png')

        figure = Image.open(img_buf)

        py_image = pygame.image.fromstring(im.tobytes(), im.size, im.mode)
        py_plot = pygame.image.fromstring(figure.tobytes(), figure.size, figure.mode)
        rect = py_image.get_rect()
        window.blit(py_image, rect)
        window.blit(py_plot, (0,260))

    pygame.display.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d]:
            end_time += SPEED
            end_time = min(end_time, sesh[-1][-1][2] - sesh[0][-1][2])
            new = True
        elif keys[pygame.K_a]:
            end_time -= SPEED
            end_time = max(end_time, 0)
            new = True
        elif keys[pygame.K_s]:
            end_time = sesh[-1][-1][2] - sesh[0][0][2] - 4.1
            end_time = max(end_time, 0)
            new = True
        elif keys[pygame.K_c]:
            end_time = sesh[-1][-1][2] - sesh[0][0][2]
            new = True
        elif keys[pygame.K_w]:
            end_time = 0
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
