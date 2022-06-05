import time as t
#from scipy.stats import linregress
from PIL import ImageDraw, Image
import mss

from sympy import Q
from model_stuff.rod_heat.rodHeatManager import RodHeatManager
from settings import *
from basicHelpers import *
from fishingHelpers import *
from humanInput import *
from videoWrite import make_video #modded https://github.com/krishnachaitanya7/pil_video/blob/main/pil_video/pil_video.py
pag.PAUSE = 0

#[25,27,26], 21,23,22,   32,28,29,   35,30,27,   41,33,30  33, 28, 32

#TIME 13

#band
#19, 41
#17, 32
#22, 32

#wood
#48, 85
#50,82
#56,79
none_type = type(None)

class Fisher(object):
    def __init__(self, var={}, maxtime = None):
        self.var = {**defaultVar, **var}
        self.maxtime = maxtime
        self.keys = []
        self.buttons = []
        self.rx = 0
        self.ry = 0
        self.dx = 0
        self.dy = 0
        self.brightness = 1.0
        self.rod_heat_manager = RodHeatManager(".\\model_stuff\\rod_heat\\rod_heat_model")

        self.last_pull_time = None
        self.last_cool_time = None

        self.last_acc_high = False

        self.fishing_left = False
        self.fishing_left_time = None
        self.first_rot = None

        self.mouse = Mouse()
        
    def rotate_to(self, rx, ry, speed=1, ignore_cap=False):
        dbg('@rotate_to',1)

        if not ignore_cap:
            rx = min(max(rx, MIN_ROT), MAX_ROT)
            ry = min(max(ry, MIN_ROT), MAX_ROT)
        #dt = t.time()
        dx = round(rx)
        dy = round(ry)
        #self.rotate(dx,dy)
        self.mouse.rotate_to(round(dx*SENSITIVITY),round(dy*SENSITIVITY),speed)
        dbg('% rotate_to',1)
        
    def reset_rotation(self):
        dbg('@rest_rotation')
        self.rotate_to(0,0)
        dbg('%reset_rotation')
    
    def add_button(self, button):
        dbg('@add_button')
        if not button in self.buttons:
            dbg('>'+button)
            self.buttons.append(button)
            pag.mouseDown(button=button)
        dbg('%add_button')
        
    def rm_button(self,button):
        dbg('@rm_button')
        if button in self.buttons:
            dbg('<' + button)
            self.buttons.remove(button)
            pag.mouseUp(button=button)
        dbg('%rm_button')
        
    def switch_keys(self, keys):
        dbg('@switch_keys ' + str(keys))
        for nk in keys:
            if not nk in self.keys:
                dbg('>'+nk,1)
                pag.keyDown(nk)
        for ok in self.keys:
            if not ok in keys:
                dbg('<'+ok,1)
                pag.keyUp(ok)
        self.keys = keys
        dbg('%switch_keys')

    def desired_keys(self):
        #print('~~desired_keys')
        return ['s','d']
        pos = self.get_bobber_estimate()
        if pos[1] < i_y(self.var['NEARPLAYER'])  or abs(pos[0] - SCREEN_SIZE[0] / 2) < i_x(self.var['CENTERWIDTH']):
            return ['s']
        else:
            keys = []
            if abs(pos[0] - SCREEN_SIZE[0] / 2) < i_x(self.var['DIAGONALWIDTH']):
                keys.append('s')
                
            if pos[0] - SCREEN_SIZE[0] / 2 > 0:
                keys.append('a')
            else:
                keys.append('d')
            return keys

    def handle_cast(self, im=None):
        dbg('@handle_cast')
        if not im:
            im = iGrab.grab()
        #im.save('dbg/wat' + str(t.time()) + '.png')
        self.rotate_to(0,0)
        self.mouse.play_thread.join()
        t.sleep(g(0.05))
        self.rotate_to(0,0)
        t.sleep(g(0.1))
        self.mouse.play_thread.join()
        self.heat = 0
        self.cooling = False
        self.brightness = get_brightness(im)
        self.band_positions = []
        self.band_track_length = 8
       
        if self.active_rod(im) == None:
            pressSlot(self.inactive_rod(im))

        if not 'right' in self.buttons:
            self.add_button('right')
            t.sleep(g(1.3))
         
        self.add_button('left')
        t.sleep(g(0.2))
        self.rm_button('left')
        t.sleep(1)
        
        self.rotate_to(g(20),3,)
        t.sleep(g(2))
        #if self.first_rot < 35:
        #    self.rotate_to(g(40))

        self.switch_keys(['s','d'])
        dbg('%handle_cast')

    def event_wait(self, event_type):
        dbg('@event_wait')
        if event_type == 'FASTSUCCESS':
            t.sleep(g(1.3))
        elif event_type == 'SUCCESS':
            t.sleep(g(8))
        elif event_type == 'TIMEOUT':
            t.sleep(g(5.3))
        elif event_type == 'FASTTIMEOUT':
            t.sleep(g(1.3))
        dbg('%event_wait')
        
    def track_band(self, im, cap_time):
        dbg('@track_band')
        debug = True

        #if self.mouse.play_thread.is_alive():
        #    dbg('%track_band - mouse movement left')
        #    return

        #if im == None:
        #    im = iGrab.grab()
        x_pos = 0
        y_pos = 0
        samples = 0
        
        chan_max = lerp(self.brightness, LINE_BRIGHTNESS_CURVE)
        def is_line(px):
            if px[0] <= chan_max and px[2] <= chan_max:
                return True
            return False
        matches = []
        dbg_scanned = 0

        def get_pos(min_x, min_y, max_x, max_y, speed_x, speed_y, min_row, draw=False):
            x_pos = 0
            y_pos = 0
            samples = 0
            for y in range(max_y, min_y, -speed_y):
                x_matches = []
                for x in range(min_x, max_x, speed_x):
                    px = im.im[y][x]
                    if is_line(px):
                        if debug and draw:
                            im.put_pixel(x,y, (0,255,0), offset=False)
                        x_matches.append((x,y))
                if len(x_matches) >= min_row:
                    for match in x_matches:
                        x_pos += match[0]
                        y_pos += match[1]
                        samples += 1
            
            return x_pos/max(1, samples), y_pos/max(1, samples), samples           
        
        dbg('&trackband start fast')

        fast_x, fast_y, fast_samples = get_pos(
            SHAKE_TL[0]-im.left,
            SHAKE_TL[1]-im.top,
            SHAKE_BR[0]-im.left,
            SHAKE_BR[1]-im.top,
            SHAKE_FAST_SPEED_X,
            SHAKE_FAST_SPEED_Y,
            2,
            True )
        fast_x += im.left
        fast_y += im.top
        dbg('&trackband done fast' + str(fast_samples))

        if fast_samples:
            max_slow_x = round(min(SHAKE_BR[0], fast_x + SHAKE_SLOW_WIDTH)) #Cap right
            min_slow_x = round(max_slow_x - SHAKE_SLOW_WIDTH * 2)
            min_slow_y = round(max(SHAKE_TL[1], fast_y - SHAKE_SLOW_HEIGHT)) # cap top
            max_slow_y = round(min_slow_y + SHAKE_SLOW_HEIGHT * 2)
        
            

            slow_x, slow_y, slow_samples = get_pos(
                min_slow_x - im.left,
                min_slow_y - im.top,
                max_slow_x - im.left,
                max_slow_y - im.top,
                SHAKE_SPEED_X,
                SHAKE_SPEED_Y,
                7,
                False)
            slow_x += im.left
            slow_y += im.top
            dbg('&trackband end slow ' +  str(slow_samples))
            if slow_samples:

                if debug:
                    im.put_pixel(round(SHAKE_TL[0]), round(SHAKE_TL[1]), (0,255,255) )
                    im.put_pixel(round(SHAKE_TL[0]), round(SHAKE_BR[1]), (0,255,255) )
                    im.put_pixel(round(SHAKE_BR[0]), round(SHAKE_TL[1]), (0,255,255) )
                    im.put_pixel(round(SHAKE_BR[0]), round(SHAKE_BR[1]), (0,255,255) )
                    im.put_pixel(round(min_slow_x), round(max_slow_y), (0,255,0) )
                    im.put_pixel(round(min_slow_x), round(min_slow_y), (0,255,0) )
                    im.put_pixel(round(max_slow_x), round(max_slow_y), (0,255,0) )
                    im.put_pixel(round(max_slow_x), round(min_slow_y), (0,255,0) )
                    im.put_pixel(round(min_slow_x), round(max_slow_y-1), (0,255,0) )
                    im.put_pixel(round(min_slow_x), round(min_slow_y+1), (0,255,0) )
                    im.put_pixel(round(max_slow_x), round(max_slow_y-1), (0,255,0) )
                    im.put_pixel(round(max_slow_x), round(min_slow_y+1), (0,255,0) )

                    
                if slow_samples == 0:
                    #self.band_positions.append((SHAKE_TL[0], SHAKE_BR[1], cap_time, samples))
                    pass
                    #if debug:
                    #    im.putpixel((1,0), (255,255,255))
                    #    im.putpixel((3,0), (255,255,255))
                
                else:
                    self.band_positions.append((slow_x, slow_y, cap_time, samples))
                    if debug:
                        im.put_pixel(round(slow_x), round(slow_y), (255,255,255) )
                        im.put_pixel(round(slow_x), round(slow_y+1), (255,255,255) )
                        im.put_pixel(round(slow_x+1), round(slow_y), (255,255,255) )
                        im.put_pixel(round(slow_x+1), round(slow_y+1), (255,255,255) )
                    #    im.putpixel((round(x_pos), round(y_pos) ), (255,255,255) )

                
                    self.band_positions = self.band_positions[-40:]
                    dbg('%track_band -- ret')
                    return (slow_x, slow_y, cap_time, samples)

    dbg('%track_band')
    
    def band_score(self):
        use = self.band_positions[-80:]
        sample_count = len(use)
        
        if sample_count < 3:
            return 0
        avgx = 0
        avgy = 0
        
        for s in self.band_positions:
            avgx += s[0]
            avgy += s[1]
        avgx /= sample_count
        avgy /= sample_count
        err = 0
        for s in self.band_positions:
            err += abs(avgy - s[1])
        err /= sample_count
        return err
            
        '''
        last_x = self.band_positions[1][0]
        last_y = self.band_positions[1][1]
        last_t = self.band_positions[1][2]

        last_dt = last_t - self.band_positions[0][2]
        last_vx = last_x - self.band_positions[0][0]/last_dt
        last_vy = last_y - self.band_positions[0][1]/last_dt

        avg_vx = 0
        avg_vy = 0
        acc = 0
        samples = 0
        vls = []
        for i in range(2, len(self.band_positions)):
            new_pos = self.band_positions[i]
            old_pos = self.band_positions[i-1]

            new_dt = new_pos[2] - old_pos[2]
            new_vx = new_pos[0] - old_pos[0] / new_dt
            new_vy = new_pos[1] - old_pos[1] / new_dt
            vls.append((new_vx, new_vy))
            avg_vx += new_vx
            avg_vy += new_vy
            samples += 1
        
        avg_vx /= samples
        avg_vy /= samples

        err = 0
        for vl in vls:
            err += (vl[0] - avg_vx) ** 2 + (vl[1] - avg_vy) ** 2

        print('RODacc', acc / samples / 100)
        return err / samples / 100000000000000'''


    def handle_pull(self):
        dbg('@handle_pull')
        def handle_event(im):
            event = self.event_check(im)
            if event:
                self.switch_keys([])
                self.event_wait(event)
                dbg('%handle_pull - event')
                return event
        
        chan_max = lerp(self.brightness, LINE_BRIGHTNESS_CURVE)
        def is_rod(px):
            if px[0] <= chan_max and px[2] <= chan_max:
                return True
        
        if self.brightness < 0.045:
            print('SKIPPING PULL\n;lllllllllllllll\nlllllllllllll')
            dbg('%handle pull - skipped')
            return None     
        
        start_time = t.time()
        while t.time() - start_time < self.var['MAXWAIT']:
            im = iGrab.grab()
            event = handle_event(im)
            if event:
                dbg('%handle_pull - event2')
                return event
            for x in range(PULLING_TL[0], PULLING_BR[0], PULLING_SCAN_SPEED):
                for y in range(PULLING_TL[1], PULLING_BR[1], PULLING_SCAN_SPEED):
                    px = im.getpixel((x,y))
                    
                    if is_rod(px):
                        print('HOOKED')
                        self.switch_keys(['s','d'])
                        '''for time_length in (self.var['FIRST_PULL_TIME'], self.var['FIRST_COOL_TIME']):
                            test_time = t.time()
                            event = None
                            while t.time() - test_time < time_length and not event:
                                im = iGrab.grab()
                                self.handle_angle_correction(im)
                                event = handle_event(im)
                                if event:
                                    dbg('%handle_pull - event3')
                                    return event
                                #t.sleep(self.var['SCANTIME'])
                                
                            self.switch_keys([])'''
                        dbg('%handle_pull - pulled')
                        return None
        dbg('%handle_pull - maxwait')
        return None
    
    def handle_angle_correction(self, sct):
        dbg('@handle_angle_correction')
        debug = True#True


        old_fishing_left = self.fishing_left

        hot_pos = slot_pos(0,0)

        vx = self.mouse.vx.value
        vy = self.mouse.vy.value

        rot = (m.radians(vy / SENSITIVITY) * 1,m.radians(vx / SENSITIVITY),0)#,0)
        snap_rot = rot[0], rot[1] - m.radians(50), rot[0]
        z_dist = min(2.3 / max(0.001, abs( m.tan(snap_rot[1])) ), 6.7)

        def handle_rotation():
            if self.fishing_left and not old_fishing_left:
                print('ROTTEATE LEFT!!!!')
                #self.switch_keys(['d'])
                self.rotate_to(-10, 0, 0.25)
                #self.band_positions = []
            elif not self.fishing_left and old_fishing_left:
                print('ROTTEATE RIGH    T!!!!')
                self.rotate_to(50, 0, 3 )
            #else:
                #print('no action', self.brightness)

        ### GET HEIGHT
        left_corner_min = [-2.3, self.var['WATER_MIN'], z_dist]
        left_corner_max = [-2.3, self.var['WATER_MAX'], z_dist]
        
        max_l = persp_proj(left_corner_max, rot)
        min_l = persp_proj(left_corner_min, rot)
        max_bright = 160 * self.brightness

        min_im_x = min(max_l[0], min_l[0])
        min_im_y = min(max_l[1], min_l[1], EVENT_GRAB_TL[1])

        max_pl = persp_proj([ -0.1, self.var['WATER_MAX'], 0.2 ], rot)
        min_pl = persp_proj([ -0.1, self.var['WATER_MIN'], 0.2 ], rot)



        max_im_x = EVENT_GRAB_BR[0]
        max_im_y = min(max(max_pl[1], min_pl[1], EVENT_GRAB_BR[1]), HOT_POS[1] - 2 ) 

        dbg('grabimg img ' + str((min_im_x, min_im_y, max_im_x, max_im_y)))
        cap_time = t.time()
        sct_im = sct.grab((min_im_x, min_im_y, max_im_x, max_im_y))
        dbg('making img ')
        np_im = np.array( sct_im) 
        cropped_im = CroppedIm(np_im, min_im_x, min_im_y)
        dbg('made img ')

        if self.fishing_left_time and t.time() - self.fishing_left_time < 2:
            dbg('%handle_angle_correction - time skip')
            return cropped_im, cap_time

        #print('R',runtime, 'sdminl', min_l, 'maxl', max_l)
        water_height_line = Line( (min_l[0] - min_im_x, min_l[1] - min_im_y ) , (max_l[0] - min_im_x, max_l[1] - min_im_y ) )

        iter_dist = 0
        line_iter = water_height_line.get_iter(WATER_HEIGHT_SPEED,0 , max_im_x - max_im_y, 0, max_im_y - min_im_y)
        water_height = 0
        
        for (x, y) in line_iter:
            #print('iter ', x,y)
            pxl = np_im[y][x]
            if dist((0,0,0), pxl) < max_bright:
                #print('R',runtime,"dist445", iter_dist)
                #print("delta", abs(line_iter.max-line_iter.min)) 
                #print("water min max", (self.var['WATER_MAX'] - self.var['WATER_MIN']) )
                #print("water min",  self.var['WATER_MIN'] )
                #print("HEIIGHT445", iter_dist / abs(line_iter.max-line_iter.min) * (self.var['WATER_MAX'] - self.var['WATER_MIN']) + self.var['WATER_MIN'] - 0.2)

                water_height = max(
                    iter_dist / abs(line_iter.max-line_iter.min) * (self.var['WATER_MAX'] - self.var['WATER_MIN']) + self.var['WATER_MIN'] - 0.2,
                    self.var['WATER_MIN']
                )
            iter_dist += WATER_HEIGHT_SPEED
        dbg('&anglecorrect - gotheight ')

        height = water_height
        #print('out 1')
        ### GET SCAN LINE

        mod_z_dist = abs((2.3+height/2 - self.var['WATER_MIN']/2) / max(0.001, abs( m.tan(snap_rot[1])) ))
        
        FISH_LEFT_P1 = [ -2.3+height/2 - self.var['WATER_MIN']/2, height, min(mod_z_dist, 6.7) ]
        FISH_LEFT_P2 = [ -0.1, height, 0.2 ]
        pp1 = persp_proj(FISH_LEFT_P1, rot)
        pp2 = persp_proj(FISH_LEFT_P2, rot)

        scan_line = Line((pp2[0] - min_im_x, pp2[1] - min_im_y), (pp1[0] - min_im_x, pp1[1] - min_im_y))
        scan_iter = scan_line.get_iter(SCAN_LINE_SPEED, 0, max_im_x - max_im_y, 0, max_im_y - min_im_y)

        if debug:
            #print('putting', max_pl, cropped_im.left, cropped_im.top)
            cropped_im.put_pixel(*max_l, (255,0,0))
            cropped_im.put_pixel(*min_l, (0,255,0))

        ### SCAN THE LINE

        chan_max = 95 * self.brightness + 0
        def is_line(x,y):
            px = np_im[y][x]
            if px[0] <= chan_max and px[2] <= chan_max:
                return True

        self.fishing_left = False

        last_pos = next(scan_iter) #None

        for x,y in scan_iter:
            #print('ITER33',x,y)
            #if hot_pos[1] < y+cropped_im.top < hot_pos[1] + SLOT_SIZE and hot_pos[0] < x+cropped_im.left < hot_pos[0] + SLOT_SIZE * 6:
            #    continue
            if debug and x % 4 == 0:
                #print('put',x+1,y )
                cropped_im.put_pixel(x+1,y, (0,0,255), False)

            #print('at2', x,y)
            if is_line(x, y):
                self.fishing_left_time = t.time()
                self.fishing_left = True
                if not debug:
                    break
            #last_pos = (x,y)
        else:
            y = last_pos[1]
            for dx in range(0,int(SCREEN_SIZE[0] * 0.5) - cropped_im.left - last_pos[0],SCAN_LINE_SPEED):
                x = last_pos[0] + dx
                pxl = np_im[y][x]
                if debug and x % 4 == 0:
                    #print('put',x+1,y )
                    cropped_im.put_pixel(x+1,y, (0,0,255), False)
                if is_line(x, y):
                    self.fishing_left_time = t.time()
                    self.fishing_left = True
                    if not debug:
                        break
            '''if debug:
                if self.fishing_left:
                    im.putpixel((x,y), (0,255,0))
                else:
                    im.putpixel((x,y), (0,0,255))'''
            
        handle_rotation()
        dbg('%handle_angle_correction - ' +str(self.fishing_left))
        return cropped_im, cap_time
        '''
        if debug:

            far_corner_max = [-2.3, self.var['WATER_MAX'], 5.8]
            right_corner_max = [0.5, self.var['WATER_MAX'], 5.8]
            left_corner_max = [-2.3, self.var['WATER_MAX'], z_dist]
            max_l = persp_proj(left_corner_max, rot)
            max_f = persp_proj(far_corner_max, rot)
            max_r = persp_proj(right_corner_max, rot)

            far_corner_min = [-2.3, self.var['WATER_MIN'], 5.8]
            right_corner_min = [0.5, self.var['WATER_MIN'], 5.8]
            left_corner_min = [-2.3, self.var['WATER_MIN'], z_dist]
            min_l = persp_proj(left_corner_min, rot)
            min_f = persp_proj(far_corner_min, rot)
            min_r = persp_proj(right_corner_min, rot)

            far_corner_0 = [-2.3, 0, 5.8]
            right_corner_0 = [0.5, 0, 5.8]
            left_corner_0 = [-2.3, 0, z_dist]
            zero_l = persp_proj(left_corner_0, rot)
            zero_f = persp_proj(far_corner_0, rot)
            zero_r = persp_proj(right_corner_0, rot)

            far_corner_scan = [-2.3,height , 5.8]
            right_corner_scan = [0.5,height , 5.8]
            left_corner_scan = [-2.3,height , z_dist]
            scan_l = persp_proj(left_corner_scan, rot)
            scan_f = persp_proj(far_corner_scan, rot)
            scan_r = persp_proj(right_corner_scan, rot)
            

            draw = ImageDraw.Draw(im)
            print('BACK PLANE POINTS, ', zero_l, zero_f, zero_r)
            draw.line((min_l, min_f), fill=(250,0,0))
            draw.line((min_f, min_r), fill=(250,0,0))

            draw.line((max_l, max_f), fill=(0,0,250))
            draw.line((max_f, max_r), fill=(0,0,250))

            draw.line((zero_l, zero_f), fill=(50,50,50))
            draw.line((zero_f, zero_r), fill=(50,50,50))

            draw.line((scan_l, scan_f), fill=(0,250,0))
            draw.line((scan_f, scan_r), fill=(0,250,0))

            im = im.crop((0,0,2560,1440))
            im.thumbnail( (2560//2,1440//2  ) , Image.NEAREST)
            if self.fishing_left:
                im.save('dbg/fff' + str(runtime) + '.png')
            else:
                im.save('dbg/ggggg' + str(runtime) + '.png')
        '''
        #im.save('dbg/asdas' + str(t.time()) + '.png')
        #sprint('FISHLEFT',self.fishing_left, 95 * self.brightness + 2, )
        #im.show()

    def update_actions(self, last_action_time):
        dbg('@update_actions')
        print('update time', last_action_time)
        if self.cooling:
            print('cooling')
            self.switch_keys([])
            self.heat -= last_action_time
            if self.heat <= 0:
                self.cooling = False
        if not self.cooling:
            self.heat += last_action_time
            desired = self.desired_keys()
            #acc = self.band_acceleration()
            if self.heat > 1 and False: #acc >= 630:
                if self.last_acc_high:
                    print('high accel',acc)
                    self.band_positions = []
                    self.cooling = True
                    self.heat = self.heat * 0.8 + 0.5
                    self.switch_keys([])
                self.last_acc_high = True
            else:
                self.last_acc_high = False
                #print('fine accel',acc)
                self.switch_keys(desired)

        '''if self.cooling:
            self.heat -= self.var['COOLTIME'] * last_action_time
            if self.heat <= 0:
                self.cooling = False

        if not self.cooling:
            desired = self.desired_keys()
            if 's' in desired:
                self.heat += self.var['HEATTIME'] * last_action_time
            if 'a' in desired or 'd' in desired:
                self.heat += self.var['SIDEHEATTIME'] * last_action_time

            if self.heat >= 1:
                self.cooling = True
                self.switch_keys([])

            else:
                self.switch_keys(desired)'''
        dbg('%update_actions')

    def event_check(self, im=None):
        dbg('@event_check')
        is_array = False
        if type(im) == none_type:
            print('EVENT GRABBING')
            im = iGrab.grab()
        elif type(im) == CroppedIm:
            is_array = True
        def rod_snapped():
            dbg('@event_check.rod_snapped')
            chan_max = lerp(self.brightness, LINE_BRIGHTNESS_CURVE)+1
            #print('rod max', chan_max)
            if is_array:
                for x in range(RAISED_ROD_TL[0] - im.left, RAISED_ROD_BR[0] - im.left, RAISED_ROD_SPEED):
                    for y in range(RAISED_ROD_TL[1] - im.top, RAISED_ROD_BR[1] - im.top, RAISED_ROD_SPEED):
                        px = im.im[y][x]
                        if px[0] <= chan_max and px[1] <= chan_max and px[2] <= chan_max:
                            #im.putpixel((x,y), (0,0,255))
                            dbg('%event_check.rod_snapped -- sapped')
                            return 'SNAP'

            else:
                for x in range(RAISED_ROD_TL[0], RAISED_ROD_BR[0], RAISED_ROD_SPEED):
                    for y in range(RAISED_ROD_TL[1], RAISED_ROD_BR[1], RAISED_ROD_SPEED):
                        #print('raised rod check',x,y, px)
                        px = im.getpixel((x,y))
                        #print('raised rod check',x,y, px)
                        #im.putpixel((x,y), (0,255,0))

                        if px[0] <= chan_max and px[1] <= chan_max and px[2] <= chan_max:
                            #im.putpixel((x,y), (0,0,255))
                            dbg('%event_check.rod_snapped -- sapped')
                            return 'SNAP'
            dbg('%event_check.rod_snapped -- nosapped')
            return None
        
        BOBBER_PASS_G_CHAN = lerp(self.brightness, [(0,18-4), (1, 36-5)] )
        BOBBER_PASS_B_CHAN = lerp(self.brightness,[(0,31-4), (1,57-5)])
        BOBBER_FAIL_R_CHAN = lerp(self.brightness,[(0,33-4), (1,56-5)])

        def rod_snapped_night():#TODO FIX NIGHT
            for x in range (BOBBER_HOLO_TL[0], BOBBER_HOLO_BR[0], BOBBER_HOLO_SPEED):
                for y in range (BOBBER_HOLO_TL[1], BOBBER_HOLO_BR[1], BOBBER_HOLO_SPEED):
                    px = im.getpixel((x,y))
                    if px[0] > BOBBER_FAIL_R_CHAN and px[0] > px[2] * 4:
                        return 'SNAP'
                    elif px[2] > BOBBER_PASS_B_CHAN and px[1] > BOBBER_PASS_G_CHAN and px[1] > px[0] * 4:
                        return 'SNAP'

        dbg('& event - got pickup check')
        if got_pickup(im): # success
            dbg('! got pickup')
            im = iGrab.grab()
            other_rod = self.inactive_rod(im)
            if other_rod != None:
                print('select second rod')
                t.sleep(g(0,0.2))
                pressSlot(other_rod)
                t.sleep(g(0.3))
                dbg('%event_check - fastsuccess')
                return 'FASTSUCCESS'
            else:
                dbg('%event_check - success')
                return 'SUCCESS'
        dbg('& event - check snap start')
        if self.brightness > 0.045:
            #print('NIGHT SNAP\n;lllllllllllllll\nlllllllllllll')
            ret =  rod_snapped()
        else:
            ret = rod_snapped_night()
        dbg('%event_check - rodsnapped=' + str(ret))
        return ret

    def estimate_heat(self, time_change):
        POINTS_LEN = 6
        if len(self.band_positions) <= POINTS_LEN:
            return -1
        
        data = [self.band_positions[-1][0],self.band_positions[-1][1], time_change]
        for samp_ind in range(0, POINTS_LEN, 1):
            samp = self.band_positions[-2-samp_ind]
            next_samp = self.band_positions[-1-samp_ind]
            dx = next_samp[0] - samp[0]
            dy = next_samp[1] - samp[1]
            dt = next_samp[2] - samp[2]
            data.append(dx)
            data.append(dy)
            data.append(dt)
        print('using data', data)
        return self.rod_heat_manager.predict(data)

    def handle_fight(self):
        dbg('@handle_fight')

        debug = True
        with mss.mss() as sct:
            start_time = t.time()
            last_time = start_time
            new_time = start_time
            last_ims = []
            itersi = 0
            datas = []
            self.band_positions = []
            #self.brightness = get_brightness(im)
            print('grabbing',(*EVENT_GRAB_TL, *EVENT_GRAB_BR))

            event_im = np.array(sct.grab((*EVENT_GRAB_TL, *EVENT_GRAB_BR)))
            cropped_im = CroppedIm(event_im, *EVENT_GRAB_TL)

            event = self.event_check(cropped_im)
            print('looping')
            while not event or new_time - start_time > self.var['MAXWAIT']:
                last_time = new_time
                new_time = t.time()
                time_change = new_time - last_time
                
                dbg('* fight loop -  last time change' +  str(time_change) + ' bright' + str(self.brightness), 0 )
                cropped_im, cap_time = self.handle_angle_correction(sct)
                
                event = self.event_check(cropped_im)

                new_pos = self.track_band(cropped_im, cap_time)
                
                if new_pos:
                    datas.append(new_pos)

                self.update_actions(time_change)

                #if itersi % 10 == 0:
                #    self.brightness = get_brightness(im)
                
                
                #datas.append(self.band_acceleration())
                if debug:
                    heat_est = self.estimate_heat(new_time-start_time)
                    print('HEAT ',heat_est)
                    try:
                        cropped_im.put_pixel(100,0, (255,255,0), False)
                        cropped_im.put_pixel(200,0, (255,255,0), False)
                        cropped_im.put_pixel(round(heat_est)+100,0, (0,255,0), False)
                        cropped_im.put_pixel(round(heat_est)+100,1, (0,255,0), False)
                        cropped_im.put_pixel(round(heat_est)+100,2, (0,255,0), False)
                    except Exception as e:
                        print('HEAT ERR', e)
                    last_ims.append( cropped_im )

                #last_ims = last_ims[-110:]
                itersi += 1
                if itersi % 1 == 0:
                    
                    print('iter time', time_change)
                #t.sleep(max(0,self.var['SCANTIME'] - time_change))
                #print('sleeping', max(0,self.var['SCANTIME'] - time_change))
            

        print('SAVE DATATE')
        if event == 'SNAP': 
            dbg('# save snap pics')
            with open('dbg\\snaps.txt', 'a+') as f:
                f.write(json.dumps(( str(start_time)[6:12] + '_' +str(event), datas)) + '\n')
                #f.write(json.dumps(str(datas[ ::-1])) + '\n')
            #for i, snap_im in enumerate(last_ims[-1:]):
            #    snap_im.save('dbg\\' + str(new_time) + '_' + str(i) + '.png')
        elif event:
            with open('dbg\\catches.txt', 'a+') as f:
                f.write(json.dumps((str(start_time)[6:12] + '_' +str(event), datas)) + '\n')

        if debug and event == 'SNAP':
            self.mouse.play_thread.join()
            
            

            #make_video([Image.fromarray(cim.im) for cim in last_ims], str(start_time)[6:12] + '.mp4')
            
            max_lx = 0
            min_lx = 9999
            max_rx = 0
            min_rx = 9999
            max_ty = 0
            min_ty = 9999
            min_by = 9999
            max_by = 0
            for cim in last_ims:
                min_lx = min(cim.left, min_lx)
                max_lx = max(cim.left, max_lx)
                max_ty = max(cim.top, max_ty)
                min_ty = min(cim.top, min_ty)
                #print('type', type(cim.im), type(cim.im.size), cim.im.size)
                max_rx = max(max_rx, cim.left + cim.im.shape[1])
                max_by = max(max_by, cim.left + cim.im.shape[0])
                min_rx = min(min_rx, cim.left + cim.im.shape[1])
                min_by = min(min_by, cim.left + cim.im.shape[0])
            fps = len(last_ims)/(t.time() - start_time)
            sims = []
            for cim in last_ims[:max(0,len(last_ims) - int(fps * 2.75))]:
                
                pim = Image.fromarray(cim.im)
                sim = Image.new('RGBA', (max_rx - min_lx, max_by - min_ty), color=(0,0,0,255))
                sim.paste(pim, (cim.left - min_lx, cim.top - min_ty   ))    
                #sim = sim.crop((min_lx-cim.left, min_ty-cim.top, cim.size[0] + max_rx - (cim.left + cim.im.size[0])  ,  cim.size[1] + max_by - (cim.top + cim.im.size[1])  ))
                sims.append(sim)

            make_video(sims, str(start_time)[6:12] + '_' +str(event) + '.mp4', fps=(round(fps  )))
            '''
            ii = 0
            for cim in last_ims:
                #print('WHY',SHAKE_TL, SHAKE_BR)
                sim = Image.fromarray(cim.im)
                sim = sim.crop((SHAKE_TL[0]-cim.left, SHAKE_TL[1]-cim.top, SHAKE_BR[0]-cim.left,SHAKE_BR[1]-cim.top))
                time_text = 'errtxt'
                if len(datas) > ii and len(datas[-1]) and len(datas[ii]):
                    time_text = str(datas[-1][-1][2] - datas[ii][-1][2])[:5]

                #sim.thumbnail(( (PULLING_BR[0]+100 -  PULLING_TL[0]+100)//2 , 3000), Image.NEAREST )
                sri = str(ii)
                sri = '0' * (3-len(sri)) + sri
                path = 'E:\\tempvideo\\fisher\\'
                path += str(start_time)[7:12] + '-' + sri + '-' + time_text + '__'+ str(event) + '.png'
                sim.save(path) # + str(score) + '__' 
                ii += 1'''
            
            print('done bs')
        dbg('%handle_fight')
        return event

    def fish(self):
        #   print('FI33333333SH LEFT')
        #self.handle_angle_correction()
        print('### cast')
        self.handle_cast()
        print('### pull wait')
        res = self.handle_pull()
        res = False
        if res:
            print('!!! EARLY FISH')
            self.reset_rotation()
            return res
        print('### start fight')
        res = self.handle_fight()
        print('### reset after', res)
        self.reset_rotation()
        return res

    def run(self, log_path= 'default_log.txt'):
        print('running...')

        def log(line):
            if log_path:
                with open(log_path, 'a+') as file:
                    file.write(line + '\n')
        run_id = r.choice('abcdefghijklmnopqrstuvwxyz') + str(r.randint(1111,9999))
        log(str({
            'type': 'START',
            'id':run_id,
            'time':t.time(),
            'var':self.var,
            }))
        t.sleep(4)
        start_time = t.time()
        new_time = start_time
        self.switch_keys([])
        total_fish = {}
        total_score = 0        
        snaps = 0
        timeouts = 0
        catches = 0
        unknowns = 0
        for ft in fish_names:
            total_fish[ft] = 0
        while not self.maxtime or new_time - start_time < self.maxtime:
            last_result = None
            for i in range(18): #range(self.var['FISHES_PER_ITER']):
                print('PROG',t.time() - start_time,'/',self.maxtime)
                self.event_wait(last_result)
                
                last_result = self.fish()
                if 'TIMEOUT' in last_result:
                    timeouts += 1
                elif 'SNAP' == last_result:
                    snaps += 1
                elif 'SUCCESS' in last_result:
                    catches += 1
                else:
                    unknowns += 1
                
            self.rm_button('right')
            self.switch_keys([])
            self.mouse.play_thread.join()
            loop_sum = self.inv_management()
            pag.press('space')
            t.sleep(g(0.6))
            
            new_score = 0
            for i, ft in enumerate(fish_names):
                total_fish[ft] += loop_sum[i]
                new_score += loop_sum[i] * fish_values[i]
            total_score += new_score

            log_time = t.time()
            passed = log_time - start_time
            log_data = {'type': 'ITER','id':run_id, 'average':total_score / passed, 'score': total_score, 'new score': new_score, 'snaps':snaps, 'timeouts':timeouts, 'catches':catches, 'unknowns':unknowns, 'fish':total_fish} 
            log(str(log_data))
            print('done loop')
            new_time = t.time()
            
        self.reset_rotation()
        return total_fish

    #TODO dupe?
    def slot_state(self, i, im=None):
        pos = slot_pos(i,0)
        print('pos',i,pos)
        full = al(pos, FULL_OFFSET)
        health = al(pos, HP_OFFSET)
        selected1 = al(
            pos,
            (HP_OFFSET[0] * 3, SLOT_SIZE - (HP_OFFSET[0] * 3))
        )
        selected2 = al(
            pos,
            (SLOT_SIZE - (HP_OFFSET[0] * 3), HP_OFFSET[0] * 3)
        )
        print(full,health, selected1, selected2)
        
        if not im:
            im = iGrab.grab()

        x,y = health
        w=HP_OFFSET[0]
        hasHealth = False
        for xi in range(x-w,x+w):
            for yi in range(y-3*w,y-w):
                px = im.getpixel((xi,yi))
                if sdist(px,(115,140,68)) < 225: #15
                    
                    hasHealth = True
                    break
        px = im.getpixel(full)
        isFull = sdist(px,(227,227,227)) < 900 #30
        
        px1 = im.getpixel(selected1)
        px2 = im.getpixel(selected2)
        selected_color = (
            SELECTED_MIN[0] + self.brightness * (SELECTED_MAX[0] - SELECTED_MIN[0]),
            SELECTED_MIN[1] + self.brightness * (SELECTED_MAX[1] - SELECTED_MIN[1]),
            SELECTED_MIN[2] + self.brightness * (SELECTED_MAX[2] - SELECTED_MIN[2]),
        )
        isSelected = sdist(px1,selected_color) < 900 and sdist(px2,selected_color) < 900
        print(hasHealth, isFull, isSelected)
        return hasHealth, isFull, isSelected

    def inactive_rod(self, im):
        if not im:
            im = iGrab.grab()
        for i in range(6):
            ss = self.slot_state(i)
            if ss[0] and ss[1] and not ss[2]:
                return i

    def active_rod(self, im):
        if not im:
            im = iGrab.grab()
        for i in range(6):
            ss = self.slot_state(i)
            if ss[0] and ss[1] and ss[2]:
                return i

    def chest_look(self, i):
        chest = CHESTS[i]
        self.rotate_to(chest[0], chest[1], ignore_cap=True)
        self.mouse.play_thread.join()
        t.sleep(0.3)

    def inv_management(self):
        debug = True
        loop_sum = manage_inventory()
        if debug:
            return loop_sum

        needs_rods = any([ slot_state(i)[0] == False for i in range(6)])
        depo = True
        for i in range(len(CHESTS)):
            if needs_rods or depo:
                self.chest_look(i)
                chest_im = open_chest()
                if chest_im:
                    if needs_rods:
                        needs_rods = not replenish_rods(chest_im)
                    if depo:
                        depo = not deposit_items(chest_im)
                pag.keyDown('tab')
                t.sleep(g(0.1))
                pag.keyUp('tab')
                t.sleep(0.5)
            else:
                break
        return loop_sum
        
if __name__ == "__main__":
    print('running fisher...')
    if 0:
        f = Fisher()
    else:
        t.sleep(3)
        f = Fisher()
        f.run()

def showr(rx,ry,w=3):
    t.sleep(w)
    f.rotate_to(rx,ry)
    f.mouse.play_thread.join()
    f.handle_angle_correction()
    f.mouse.play_thread.join()
    print('DONE')
