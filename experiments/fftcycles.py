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

    '''if debug:
        plt.title('band_fft')
        plt.plot(k, f_x, label='fx')
        plt.plot(k, f_y, label='fy')
        plt.show()'''
    
    return f_x, f_y, k

if __name__ == '__main__':
    
    catch_points = []
    catch_dict = {}

    with open('..\dbg\\catches.txt', 'r') as ff:
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
    with open('..\dbg\\snaps.txt', 'r') as ff:
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
    
    snap_points = []
    for vi in range(12):
        snap_points.append([])
        for ti in range(120):
            snap_points[-1].append([])
            for i in range(ti, ti+16):
                snap_points[-1][-1].append([m.cos(i/16 * 2 * 3.14159265), m.cos(i/16 * 2 * 4 * 3.14159265), 0.03 * i])

    catch_points = []
    for vi in range(12):
        catch_points.append([])
        for ti in range(120):
            catch_points[-1].append([])
            for i in range(ti, ti+16):
                catch_points[-1][-1].append([m.cos(i/16 * 2 * 3.14159265) + 1/16 * i, m.cos(i/16 * 2 * 4 * 3.14159265) + 1/16 * i, 0.03 * i])
    
    cutt = 16
    WINDOW_SIZE =  1200, 800
    SPEED = 0.025
    window = pygame.display.set_mode( WINDOW_SIZE )
    clock = pygame.time.Clock()
    new = True
    playing = False
    end_time = 0
    wiggle_var = 0.5

    snap_points.sort(key = (lambda x: x[0][0][2] - x[-1][-1][2]  ))
    snap_points = snap_points[::-1]
    inv_snap_points = snap_points[::-1]

    catch_points.sort(key = (lambda x: x[0][0][2] - x[-1][-1][2]  ))
    catch_points = catch_points[::-1]
    inv_catch_points = catch_points[::-1]

    while True:
        t1 = t.time()
        clock.tick(60)
        if playing:
            new = True
            end_time += SPEED
            if end_time >= sesh[-1][-1][2] - sesh[0][-1][2]:
                end_time = 0
        

        if new:
            print(end_time)
            view_types = {'CATCH':catch_dict, 'SNAP':snap_dict}
            #print('type', view_type, 'ind', view_ind)
            #seshname = list(view_types[view_type])[view_ind]
            sesh = snap_points[0]

            #prefixed = [filename for filename in os.listdir('E:\\tempvideo\\fisher\\') if filename.startswith(seshname)]
            
            new = False
            window.fill((0,0,0))


            py_image = Image.open(r"C:\Users\Monchy\Documents\RustFishingBot\rust\1440p_quality2\rod_mapv2.png")
            py_image = pygame.image.fromstring(py_image.tobytes(), py_image.size, py_image.mode)
            rect = py_image.get_rect()
            #window.blit(py_image, (rect[0]+346, rect[1]+114, rect[2], rect[3]))

            im = None
            chosen = None
            for i, snap in enumerate(sesh):
                print('SESH',snap)
                if end_time <= snap[-1][2] - sesh[0][0][2]:
                    #im = Image.open('E:\\tempvideo\\fisher\\' + prefixed[i])
                    chosen = snap[-cutt:]
                    break

            if chosen == None or len(chosen) < 5:
                print('TO SMALL')
                continue

            fig = plt.figure()
            N = len(chosen)



            f_x, f_y, f_t = band_fft( chosen )
            f_x0, f_y0, f_t0 = band_fft( chosen , False)
            #score = band_shake(f_x, f_y, [1,1,1])

            ax = fig.add_subplot(1, 1, 1)

            ax.plot(f_t, f_y, color=(1,0.5,0,1))
            ax.plot([7 / 16 * i for i in range(16)], [p[1] for p in snap], color=(0.7,0,0,1))
            
            ax.plot(f_t, f_x, color=(0,0.5,1,1))
            ax.plot([7 / 16 * i for i in range(16)], [p[0] for p in snap], color=(0,0,0.7,1))
            
            
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png')
            figure = Image.open(img_buf)
            plt.close(fig)
            #py_image = pygame.image.fromstring(im.tobytes(), im.size, im.mode)
            py_plot = pygame.image.fromstring(figure.tobytes(), figure.size, figure.mode)
            rect = py_image.get_rect()
            #window.blit(py_image, rect)
            window.blit(py_plot, (0,260))

            def get_col(ind, seshind, max, cutt):
                #ratio = (seshind + 1) / max
                ratio = 1#(ind + 1) / cutt
                rgb = 255 * ratio, 0, 0#255 * (1-ratio)

                return rgb
                ind += 1
                time += 1
                r = 0
                g = 0
                b = 0
                while (r,g,b) == (0,0,0):
                    if ind <= 0:
                        print('RGB ERR')
                        return (128,128,128)
                    if ind & 1:
                        r = 255
                    if ind & 2:
                        g = 255
                    if ind & 4:
                        b = 255
                    ind = ind // 8
                
                return r , g  ,b 


            
            amnt_lines = 2
            start_indsp = []
            start_indsn = []
            for sesh in inv_snap_points[:amnt_lines]:
                for i, snap in enumerate(sesh):
                    if end_time < snap[-1][2] - sesh[0][0][2]:
                        start_indsn.append(i)
                        break
                else:
                    start_indsn.append(None)


            
            for sesh in snap_points[:amnt_lines]:
                for i, snap in enumerate(sesh):
                    if end_time < snap[-1][2] - sesh[0][0][2]:
                        start_indsp.append(i)
                        break
                else:
                    start_indsp.append(None)


            start_indsm = []
            for sesh in snap_points[len(snap_points)//2 - amnt_lines // 2:len(snap_points)//2 + amnt_lines // 2]:
                for i, snap in enumerate(sesh):
                    if end_time < snap[-1][2] - sesh[0][0][2]:
                        start_indsm.append(i)
                        break
                else:
                    start_indsm.append(None)
            
            all_inds = []
            for sesh in snap_points:
                for i, snap in enumerate(sesh):
                    if end_time < snap[-1][2] - sesh[0][0][2]:
                        all_inds.append(i)
                        break
                else:
                    all_inds.append(None)

            all_inds_catch = []
            for sesh in catch_points:
                for i, catch in enumerate(sesh):
                    if end_time < catch[-1][2] - sesh[0][0][2]:
                        all_inds_catch.append(i)
                        break
                else:
                    all_inds_catch.append(None)

            for i, sesh in enumerate(snap_points):
                if all_inds[i] != None and all_inds[i] + i < len(sesh):
                    snap_ind = i+all_inds[i]
                    snapshot = sesh[snap_ind]
                    
                    start_pos = len(snapshot) -min(cutt, len(snapshot)-1)
                    for j, pos in enumerate(snapshot[-min(cutt, len(snapshot)-1):-1]):
                        #print('pos',pos,str(datas[:2])[:300] )
                        if pos[2] < sesh[-1][-1][2] - 4.2:
                            #print(pos)

                            col = int((i / len(snap_points)) * 5)
                            rgb = None
                            if col == 0:
                                rgb = 255/cutt * (j+1),0,0
                            elif col == 1:
                                rgb = 230/cutt * (j+1),230/cutt * (j+1),0
                            elif col == 2:
                                rgb = 0,255/cutt * (j+1),0
                            elif col == 3:
                                rgb = 0,150/cutt * (j+1),150/cutt * (j+1)
                            elif col == 4:
                                rgb = 0,0,255/cutt * (j+1)
                            elif col == 5:
                                rgb = 230/cutt * (j+1),0,230/cutt * (j+1)

                            pygame.draw.line(window, rgb, (  (pos[0]-1596)  , (pos[1]-735)) , ((snapshot[start_pos + j+1][0]-1596), (snapshot[start_pos + j+1][1]-735)))
            pygame.draw.line(window, (255,255,255), (  (1700-1596)  , (900-735)) , ((1800-1596), (900-735)))
            '''
            for i, sesh in enumerate(catch_points):
                if all_inds_catch[i] != None and all_inds_catch[i] + i < len(sesh):
                    snap_ind = i+all_inds_catch[i]
                    snapshot = sesh[snap_ind]
                    
                    start_pos = len(snapshot) -min(cutt, len(snapshot)-1)
                    for j, pos in enumerate(snapshot[-min(cutt, len(snapshot)-1):-1]):
                        #print('pos',pos,str(datas[:2])[:300] )
                        if pos[2] < sesh[-1][-1][2]:
                            #print(pos)

                            col = int((i / len(catch_points)) * 5)
                            rgb = None
                            if col == 0:
                                rgb = 255/cutt * j,0,0
                            elif col == 1:
                                rgb = 230/cutt * j,230/cutt * j,0
                            elif col == 2:
                                rgb = 0,255/cutt * j,0
                            elif col == 3:
                                rgb = 0,150/cutt * j,150/cutt * j
                            elif col == 4:
                                rgb = 0,0,255/cutt * j
                            elif col == 5:
                                rgb = 230/cutt * j,0,230/cutt * j

                            pygame.draw.line(window, rgb, (  2*(pos[0]-1596)  , 2*(pos[1]-735)) , (2*(snapshot[start_pos + j+1][0]-1596), 2*(snapshot[start_pos + j+1][1]-735)))
            ''' 

                    
            '''for i, sesh in enumerate(snap_points[:amnt_lines]):
                if start_indsp[i] != None and start_indsp[i] + i < len(sesh):
                    snap_ind = i+start_indsp[i]
                    snapshot = sesh[snap_ind]
                    
                    start_pos = len(snapshot) -min(cutt, len(snapshot)-1)
                    for j, pos in enumerate(snapshot[-min(cutt, len(snapshot)-1):-1]):
                        #print('pos',pos,str(datas[:2])[:300] )
                        if pos[2] < sesh[-1][-1][2] - 4.2:
                            #print(pos)
                            pygame.draw.line(window, (255/cutt * j,0,0,128), (  2*(pos[0]-1596)  , 2*(pos[1]-735)) , (2*(snapshot[start_pos + j+1][0]-1596), 2*(snapshot[start_pos + j+1][1]-735)))
            for i, sesh in enumerate(snap_points[len(snap_points)//2 - amnt_lines // 2:len(snap_points)//2 + amnt_lines // 2]):
                if start_indsm[i] != None and start_indsm[i] + i < len(sesh):
                    snap_ind = i+start_indsm[i]
                    snapshot = sesh[snap_ind]
                    
                    start_pos = len(snapshot) -min(cutt, len(snapshot)-1)
                    for j, pos in enumerate(snapshot[-min(cutt, len(snapshot)-1):-1]):
                        #print('pos',pos,str(datas[:2])[:300] )
                        if pos[2] < sesh[-1][-1][2] - 4.2:
                            pygame.draw.line(window, (0,255/cutt * j,0,128), (  2*(pos[0]-1596)  , 2*(pos[1]-735)) , (2*(snapshot[start_pos + j+1][0]-1596), 2*(snapshot[start_pos + j+1][1]-735)))
            for i, sesh in enumerate(inv_snap_points[:amnt_lines]):
                if start_indsn[i] != None and start_indsn[i] + i < len(sesh):
                    snap_ind = i+start_indsn[i]
                    snapshot = sesh[snap_ind]
                    
                    start_pos = len(snapshot) -min(cutt, len(snapshot)-1)
                    for j, pos in enumerate(snapshot[-min(cutt, len(snapshot)-1):-1]):
                        #print('pos',pos,str(datas[:2])[:300] )
                        if pos[2] < sesh[-1][-1][2] - 4.2:
                            pygame.draw.line(window, (0,0,255/cutt * j,128), (2*(pos[0]-1596), 2*(pos[1]-735)) , (2*(snapshot[start_pos+j+1][0]-1596), 2*(snapshot[start_pos + j+1][1]-735)))
                            '''

        #print('time', t.time()-t1)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_d]:
                end_time += SPEED
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
