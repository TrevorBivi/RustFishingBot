from model_stuff.rod_heat.rodHeatManager import RodHeatManager

from rotate_vector import *
import time as t
#from scipy.stats import linregress
from PIL import ImageDraw, Image
import mss
import cProfile

from sympy import Q

from settings import *
from basicHelpers import *
from fishingHelpers import *
from humanInput import *
from videoWrite import make_video #modded https://github.com/krishnachaitanya7/pil_video/blob/main/pil_video/pil_video.py
pag.PAUSE = 0
from plane_intersect import *

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
        self.rod_heat_manager = RodHeatManager(".\\model_stuff\\rod_heat\\jun7v3.pickle")
        #del self.rod_heat_manager.model
        self.last_pull_time = None
        self.last_cool_time = None

        self.last_acc_high = False

        self.fishing_left = False
        self.fishing_left_time = None
        self.first_rot = None

        self.mouse = Mouse()
        self.heats = []
        self.temp_heat_tracker = False

        self.temp_min_time = 0.2
        self.temp_max_time = 0.75
        self.temp_time = 0.5
        self.temp_stopped = True
        
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
        #dbg('% rotate_to',1)
        
    def reset_rotation(self):
        dbg('@rest_rotation')
        self.rotate_to(0,0)
        #dbg('%reset_rotation')
    
    def add_button(self, button):
        dbg('@add_button')
        if not button in self.buttons:
            dbg('>'+button)
            self.buttons.append(button)
            pag.mouseDown(button=button)
        #dbg('%add_button')
        
    def rm_button(self,button):
        dbg('@rm_button')
        if button in self.buttons:
            dbg('<' + button)
            self.buttons.remove(button)
            pag.mouseUp(button=button)
        #dbg('%rm_button')
        
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
        #dbg('%switch_keys')

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
        self.last_pull_time = None
        self.angle_correction_time = None
        self.last_angle_result = None
       
        if self.active_rod(im) == None:
            pressSlot(self.inactive_rod(im))

        if not 'right' in self.buttons:
            self.add_button('right')
            t.sleep(g(1.3))
         
        self.add_button('left')
        t.sleep(g(0.2))
        self.rm_button('left')
        t.sleep(1)
        
        self.rotate_to(g(25),3,)
        t.sleep(g(2))
        #if self.first_rot < 35:
        #    self.rotate_to(g(40))

        self.switch_keys(['s','d'])
        #dbg('%handle_cast')

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
        #dbg('%event_wait')
    
    def rod_blue_max(self):
        rod_max = (RGB_WEIGHTS[0] * self.brightness_rgb[0] +
            RGB_WEIGHTS[1] * self.brightness_rgb[1] +
            RGB_WEIGHTS[2] * self.brightness_rgb[2] + RGB_OFFSET)
        print('rodmax',rod_max)
        return rod_max

    def water_blue_min(self):
        water_min = (WTR_WEIGHTS[0] * self.brightness_rgb[0] +
            WTR_WEIGHTS[1] * self.brightness_rgb[1] +
            WTR_WEIGHTS[2] * self.brightness_rgb[2] + WTR_OFFSET)
        return water_min

    def track_band(self, im, cap_time):
        dbg('@track_band')
        debug = True

        #if self.mouse.play_thread.is_alive():
        #    dbg('%track_band - mouse movement left')
        #    return

        #if im == None:
        #    im = iGrab.grab()

        blue_max = self.rod_blue_max()

        matches = []
        dbg_scanned = 0

        def get_pos(min_x, min_y, max_x, max_y, speed_x, speed_y, min_row, draw=False):
            x_pos = 0
            y_pos = 0
            samples = 0
            for y in range(max_y, min_y, -speed_y):
                x_matches = []
                for x in range(min_x, max_x, speed_x):
                    try:
                        px = im.im[y][x]
                    except IndexError as e:
                        print('ERR ',x,y,px)
                        raise e
                    if px[0] <= blue_max:
                        if debug and draw:
                            im.put_pixel(x,y, (0,255,0), offset=False)
                        x_matches.append((x,y))
                if len(x_matches) >= min_row:
                    for match in x_matches:
                        x_pos += match[0]
                        y_pos += match[1]
                        samples += 1
            
            return x_pos/max(1, samples), y_pos/max(1, samples), samples           
        
        #dbg('&trackband start fast')

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
        #dbg('&trackband done fast' + str(fast_samples))

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
            #dbg('&trackband end slow ' +  str(slow_samples))
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
                    self.band_positions.append((slow_x, slow_y, cap_time, slow_samples))
                    if debug:
                        im.put_pixel(round(slow_x), round(slow_y), (255,255,255) )
                        im.put_pixel(round(slow_x), round(slow_y+1), (255,255,255) )
                        im.put_pixel(round(slow_x+1), round(slow_y), (255,255,255) )
                        im.put_pixel(round(slow_x+1), round(slow_y+1), (255,255,255) )
                    #    im.putpixel((round(x_pos), round(y_pos) ), (255,255,255) )

                
                    self.band_positions = self.band_positions[-40:]
                    #dbg('%track_band -- ret')
                    return (slow_x, slow_y, cap_time, slow_samples)
    #dbg('%track_band')

    def handle_pull(self, max_wait = None):
        if max_wait == None:
            max_wait = self.var['MAXWAIT']
        dbg('@handle_pull')

        self.brightness_rgb = (0,0,0)

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
            #dbg('%handle pull - skipped')
            return None

        
        
        start_time = t.time()
        with mss.mss() as sct:
            while t.time() - start_time < max_wait:
                im = np.array(sct.grab((HOT_POS[0]-4, PULLING_TL[1] - 4, *SCREEN_SIZE)))
                im = CroppedIm(im, HOT_POS[0]-4, PULLING_TL[1] - 4)
                event = handle_event(im)
                if event:
                    print('bandsaevent')
                    #dbg('%handle_pull - event2')
                    return event
                
                blue_max = self.rod_blue_max()
                rav = 0
                gav = 0
                bav = 0
                samps = 0
                band_samps = 0
                for x in range(PULLING_TL[0], PULLING_BR[0], PULLING_SCAN_SPEED):
                    for y in range(PULLING_TL[1], PULLING_BR[1], PULLING_SCAN_SPEED):
                        px = im.get_pixel(x,y)
                        if px[2] <= blue_max:
                            band_samps +=1
                            if band_samps >= 25:
                                print('band samps +3',x,y,px)
                                self.last_pull_time = t.time()
                                self.switch_keys(['s','d'])

                                im.put_pixel(x-1,y,(255,0,0))
                                pilim = Image.fromarray(im.im)
                                pilim.save('.\\dbg\\pullstarg.png')
                                return None
                        else:
                            rav += px[0]
                            gav += px[1]
                            bav += px[2]
                            samps += 1

                self.brightness_rgb = rav/samps, gav/samps, bav/samps
                print('brightness',self.brightness_rgb)
            #dbg('%handle_pull - maxwait')
            print('nabddswhatever')
            return None

    def angle_test2(self,sct):
        debug = True
        
        vx = self.mouse.vx.value
        vy = self.mouse.vy.value
        player_rot = (
            m.radians(vy / SENSITIVITY) + m.radians(17.3),
            m.radians(vx / SENSITIVITY) - m.radians(20.5),
            0)#,0)

        ''' 
        |\ |
        | \|p-50
        '''
        far_rot = player_rot[1] - m.radians(30)
        #print('far rpt', far_rot)
        x_ops = -2.3
        #print('or zadj',-x_ops / max(m.tan(far_rot), 0.01))
        z_adj = x_ops / min(m.tan(far_rot), -0.01)
        #print('zadk',z_adj)
        z_adj = min(z_adj, 6.5)

        far_p3_max = [x_ops, self.var['WATER_MAX'], z_adj]
        far_p3_min = [x_ops, self.var['WATER_MIN'], z_adj]
        far_p2_max = persp_proj(far_p3_max, player_rot)
        far_p2_min = persp_proj(far_p3_min, player_rot)

        min_im_x = min(far_p2_max[0], far_p2_min[0])
        min_im_y = min(far_p2_max[1], EVENT_GRAB_TL[1])
        max_im_x = EVENT_GRAB_BR[0]
        max_im_y = HOT_POS[1] - 2

        bbox = (min_im_x, min_im_y, max_im_x, max_im_y+10)
        cap_time = t.time()
        sct_im = sct.grab(bbox)
        #print('bbox',bbox)
        np_im = np.array(sct_im) 
        cropped_im = CroppedIm(np_im, min_im_x, min_im_y)
        dbg('grabbed image')
        after_cap_time = t.time()

        water_height_line = Line(
            (far_p2_min[0] - min_im_x, far_p2_min[1] - min_im_y),
            (far_p2_max[0] - min_im_x, far_p2_max[1] - min_im_y)
        )
        iter_dist = 0
        line_iter = water_height_line.get_iter(
            WATER_HEIGHT_SPEED,
            0,
            max_im_x - max_im_y,
            0,
            max_im_y - min_im_y)
        max_bright = 160 * self.brightness

        water_blue_min = self.water_blue_min()
        water_height = None
        far_p2 = None
        far_p3 = None
        for (x, y) in line_iter:
            #print('iter ', x,y)
            pxl = cropped_im.im[y][x]
            if dist((0,0,0), pxl) < max_bright:
                if water_height == None:
                    d_water = iter_dist / abs(line_iter.max-line_iter.min)
                    d_max = (self.var['WATER_MAX'] - self.var['WATER_MIN'])

                    far_p3 = [far_p3_min[i] * (1-d_water) + far_p3_max[i] * d_water for i in range(3)]
                    far_p2 = (x+min_im_x,y+min_im_y)
                    water_height = max(
                     d_water * d_max + self.var['WATER_MIN'],
                    self.var['WATER_MIN']
                    )
                    cropped_im.put_pixel(x,y, (0,255,0), False)
                else:
                    cropped_im.put_pixel(x,y, (255,0,0), False)
            else:
                cropped_im.put_pixel(x,y, (0,0,255), False)
            iter_dist += WATER_HEIGHT_SPEED
        
        if water_height == None:
            water_height = self.var['WATER_MAX']
            far_p2 = far_p2_max
            far_p3 = far_p3_max

        def gen_line(rot, near_dist=1, max_dist = 99):
            near_rot = player_rot[1] - m.radians(rot)
            near_p3 = [near_dist * m.sin(near_rot), water_height, near_dist * m.cos(near_rot)]
            
            dist3 = dist(far_p3, near_p3)
            used_far_p3 = None
            if dist3 > max_dist:
                dist_ratio = max_dist / dist3
                used_far_p3 = [ far_p3[i] * dist_ratio + near_p3[i] * (1 - dist_ratio) for i in range(3)]
                used_far_p2 = persp_proj(used_far_p3, player_rot)
            else:
                used_far_p2 = far_p2

            near_p2 = persp_proj(near_p3, player_rot)
            offset_dist = 20
            delta_ftn = (used_far_p2[0] - near_p2[0]), (used_far_p2[1] - near_p2[1])
            dist_ftn = dist(used_far_p2, near_p2)
            use_dist = dist_ftn - offset_dist


            offset_far_p2 = (
                near_p2[0] + delta_ftn[0] * use_dist / dist_ftn,
                near_p2[1] + delta_ftn[1] * use_dist / dist_ftn
            )
            scan_line = Line((near_p2[0] - min_im_x, near_p2[1] - min_im_y), (offset_far_p2[0] - min_im_x, offset_far_p2[1] - min_im_y))
            return scan_line, used_far_p3, near_p3

        def scan_line(scan_line, crop, dbgcol1=(255,0,0), dbgcol2=(0,0,255)):
            
            scan_iter = scan_line.get_iter(SCAN_LINE_SPEED, 0, max_im_x - min_im_x, 0, max_im_y - min_im_y)
            
            
            #print('NOW', near_p3, used_far_p3)

            try:
                bottom_pos = next(scan_iter) #None
            except StopIteration:
                bottom_pos = 1, cropped_im.im.shape[0]-1

            hit = False
            for x,y in scan_iter:
                px = cropped_im.im[y][x]
                if px[0] < water_blue_min:
                    hit = True
                    cropped_im.put_pixel(x+1, y, dbgcol1, False)
                    if not debug:
                        break
                else:
                    cropped_im.put_pixel(x+1, y, dbgcol2, False)
            else:
                if not crop:
                    y = bottom_pos[1]
                    for dx in range(0,int(SCREEN_SIZE[0] * 0.45) - cropped_im.left - bottom_pos[0],SCAN_LINE_SPEED):
                        x = bottom_pos[0] + dx
                        px = cropped_im.im[y][x]
                        if px[0] <= water_blue_min:
                            hit = True
                            cropped_im.put_pixel(x+1, y, dbgcol1, False)
                            if not debug:
                                break
                        else:
                            cropped_im.put_pixel(x+1, y, dbgcol2, False)
            return hit
        
        def scan_dist(scan_dist,scan_far_p3,scan_near_p3,min_ang=-50,max_ang=30):
            scan_far_p3 = scan_far_p3 or far_p3
            line_dist = dist(scan_far_p3, scan_near_p3)
            if line_dist > scan_dist:
                u = [scan_dist / line_dist * (scan_far_p3[i] - scan_near_p3[i]) for i in range(3)]
                print('bigline', u)
            else:
                u = [-x_ops,water_height, (scan_dist ** 2 - (x_ops)**2)**0.5 ]
                print('smalllie', u)

            scan_2d = persp_proj(u,player_rot)
            while scan_2d[0] < 1420:
                if scan_2d[0] <= min_im_x or not (min_im_y < scan_2d[1] < max_im_y):
                    print('scipping',
                    scan_2d,
                    (min_im_x, min_im_y),
                    (max_im_x, max_im_y))
                else:
                    print('putting in', scan_2d)
                    cropped_im.put_pixel(*scan_2d, (0,255,255))
                rt = m.radians(4)
                u = [
                    u[0] * m.cos(rt) - u[2] * m.sin(rt),
                    u[1],
                    u[2] * m.cos(rt) + u[0] * m.sin(rt)
                    ]
                print('usc',u)
                scan_2d = persp_proj(u,player_rot)
          

        soft_line, soft_far_p3, soft_near_p3 = gen_line(-10)

        scan_ready = self.angle_correction_time == None or cap_time < self.angle_correction_time
        if scan_ready or self.last_angle_result != 'LEFT':
            hard_line, hard_far_p3, hard_near_p3 = gen_line(4, max_dist=3.5)
            hits_hard = scan_line(hard_line, crop=True)
            if hits_hard:
                self.rotate_to(MIN_ROT,0,0.64)
                self.last_angle_result = 'LEFT'
                self.angle_correction_time = cap_time + 1.5
                scan_ready = False

        if scan_ready:   
            if self.mouse.play_thread == None or not self.mouse.play_thread.is_alive():
                hits_soft = scan_line(soft_line, crop=False, dbgcol1=(140,20,20), dbgcol2=(20,20,140))
                if hits_soft:
                    self.rotate_to( m.degrees(player_rot[1])+20.5 - 10, m.degrees(player_rot[0]), 0.6)
                    self.last_angle_result = 'SOFTLEFT'
                    self.angle_correction_time = cap_time + 1.5
                elif self.last_angle_result != 'RIGHT':
                    self.rotate_to(MAX_ROT, 0, 3)
                    self.last_angle_result = 'RIGHT'
                    self.angle_correction_time = None
        scan_dist(1.5,soft_far_p3, soft_near_p3)
        scan_dist(3,soft_far_p3, soft_near_p3)

        return cropped_im, cap_time, after_cap_time

    def angle_test3(self,sct,move=True, rotx = 0, roty = 0, sensx=1, sensy=1, e=display_surface, camx=0, camy=1.5, camz=0):
        debug = True
        
        vx = self.mouse.vx.value
        vy = self.mouse.vy.value
        player_rot = (
            m.radians(vy / SENSITIVITY / sensy) + m.radians(19 + roty),
            m.radians(vx / SENSITIVITY / sensx) - m.radians(21.5 + rotx),
            0)#,0)

        ''' 
        |\ |
        | \|p-50
        '''
        far_rot = player_rot[1] - m.radians(30)
        #print('far rpt', far_rot)
        x_ops = -2.3
        #print('or zadj',-x_ops / max(m.tan(far_rot), 0.01))
        z_adj = x_ops / min(m.tan(far_rot), -0.01)
        #print('zadk',z_adj)
        z_adj = min(z_adj, 6.5)
        x_right = 0.35

        far_p3_max = [x_ops, self.var['WATER_MAX'], z_adj]
        far_p3_min = [x_ops, self.var['WATER_MIN'], z_adj]
        far_p2_max = persp_proj(far_p3_max, player_rot)
        far_p2_min = persp_proj(far_p3_min, player_rot)

        min_im_x = min(far_p2_max[0], far_p2_min[0])
        min_im_y = min(far_p2_max[1], EVENT_GRAB_TL[1])
        max_im_x = EVENT_GRAB_BR[0]
        max_im_y = HOT_POS[1] - 2

        min_im_x = 100
        min_im_y = 1440 - 1000
        max_im_x = 100 + 1850
        max_im_y = 1440

        bbox = (min_im_x, min_im_y, max_im_x, max_im_y+10)
        cap_time = t.time()
        #print('bboxxxx',bbox, far_p2_max[0], far_p2_min[0], far_p3_max, far_p3_min)
        sct_im = sct.grab(bbox)
        #print('bbox',bbox)
        np_im = np.array(sct_im) 
        cropped_im = CroppedIm(np_im, min_im_x, min_im_y)
        dbg('grabbed image')
        after_cap_time = t.time()

        water_height_line = Line(
            (far_p2_min[0] - min_im_x, far_p2_min[1] - min_im_y),
            (far_p2_max[0] - min_im_x, far_p2_max[1] - min_im_y)
        )
        iter_dist = 0
        line_iter = water_height_line.get_iter(
            WATER_HEIGHT_SPEED,
            0,
            max_im_x - max_im_y,
            0,
            max_im_y - min_im_y)
        max_bright = 160 * self.brightness

        water_blue_min = self.water_blue_min()#need new wall col this is for line
        water_height = None
        far_p2 = None
        far_p3 = None
        for (x, y) in line_iter:
            #print('iter ', x,y)
            pxl = cropped_im.im[y][x]
            if dist((0,0,0), pxl) < max_bright:
                if water_height == None:
                    d_water = iter_dist / abs(line_iter.max-line_iter.min)
                    d_max = (self.var['WATER_MAX'] - self.var['WATER_MIN'])

                    far_p3 = [far_p3_min[i] * (1-d_water) + far_p3_max[i] * d_water for i in range(3)]
                    far_p2 = (x+min_im_x,y+min_im_y)
                    water_height = max(
                     d_water * d_max + self.var['WATER_MIN'],
                    self.var['WATER_MIN']
                    )
                    cropped_im.put_pixel(x,y, (0,255,0), False)
                else:
                    cropped_im.put_pixel(x,y, (255,0,0), False)
            else:
                cropped_im.put_pixel(x,y, (0,0,255), False)
            iter_dist += WATER_HEIGHT_SPEED
        
        if water_height == None:
            water_height = self.var['WATER_MAX']
            far_p2 = far_p2_max
            far_p3 = far_p3_max
        
        def gen_line(rot, near_dist=1, max_dist = 99):
            near_rot = player_rot[1] - m.radians(rot)
            near_p3 = [near_dist * m.sin(near_rot), water_height, near_dist * m.cos(near_rot)]
            
            dist3 = dist(far_p3, near_p3)
            used_far_p3 = None
            if dist3 > max_dist:
                dist_ratio = max_dist / dist3
                used_far_p3 = [ far_p3[i] * dist_ratio + near_p3[i] * (1 - dist_ratio) for i in range(3)]
                used_far_p2 = persp_proj(used_far_p3, player_rot)
            else:
                used_far_p2 = far_p2

            near_p2 = persp_proj(near_p3, player_rot)
            offset_dist = 20
            delta_ftn = (used_far_p2[0] - near_p2[0]), (used_far_p2[1] - near_p2[1])
            dist_ftn = dist(used_far_p2, near_p2)
            use_dist = dist_ftn - offset_dist


            offset_far_p2 = (
                near_p2[0] + delta_ftn[0] * use_dist / dist_ftn,
                near_p2[1] + delta_ftn[1] * use_dist / dist_ftn
            )
            scan_line = Line((near_p2[0] - min_im_x, near_p2[1] - min_im_y), (offset_far_p2[0] - min_im_x, offset_far_p2[1] - min_im_y))
            return scan_line, used_far_p3, near_p3

        def scan_line(scan_line, crop, dbgcol1=(255,0,0), dbgcol2=(0,0,255)):
            
            scan_iter = scan_line.get_iter(SCAN_LINE_SPEED, 0, max_im_x - min_im_x, 0, max_im_y - min_im_y)
            
            
            #print('NOW', near_p3, used_far_p3)

            try:
                bottom_pos = next(scan_iter) #None
            except StopIteration:
                bottom_pos = 1, cropped_im.im.shape[0]-1

            hit = False
            for x,y in scan_iter:
                px = cropped_im.im[y][x]
                if px[0] < water_blue_min:
                    hit = True
                    cropped_im.put_pixel(x+1, y, dbgcol1, False)
                    if not debug:
                        break
                else:
                    cropped_im.put_pixel(x+1, y, dbgcol2, False)
            else:
                if not crop:
                    y = bottom_pos[1]
                    for dx in range(0,int(SCREEN_SIZE[0] * 0.45) - cropped_im.left - bottom_pos[0],SCAN_LINE_SPEED):
                        x = bottom_pos[0] + dx
                        px = cropped_im.im[y][x]
                        if px[0] <= water_blue_min:
                            hit = True
                            cropped_im.put_pixel(x+1, y, dbgcol1, False)
                            if not debug:
                                break
                        else:
                            cropped_im.put_pixel(x+1, y, dbgcol2, False)
            return hit
        
        def scan_pos(line_far_p3, line_near_p3, x_offset):
            dz_dx_ratio = -(line_near_p3[2] - line_far_p3[2])/(line_near_p3[0]-line_far_p3[0])
            new_far_p3 = [line_far_p3[0], line_far_p3[1], line_far_p3[2] + dz_dx_ratio * x_offset]
            
            if line_near_p3[0] + x_offset < x_right:
                new_near_p3 = [
                    line_near_p3[0] + x_offset,
                    line_near_p3[1],
                    line_near_p3[2]]
            else:        
                new_near_p3 = [
                x_right,
                line_far_p3[1],
                line_near_p3[2] + dz_dx_ratio * (x_offset + line_near_p3[0] - x_right)]

            new_far_p2 = persp_proj(new_far_p3, player_rot)
            new_far_p2 = [new_far_p2[0] - min_im_x, new_far_p2[1] - min_im_y]
            new_near_p2 = persp_proj(new_near_p3, player_rot)
            new_near_p2 = [new_near_p2[0] - min_im_x, new_near_p2[1] - min_im_y]
            
            line = Line(new_near_p2, new_far_p2)
            line_iter = line.get_iter(3, 0, max_im_x-min_im_x, 0, max_im_y-min_im_y)
            scanned = False
            for (x,y) in line_iter:
                #print(x,y)
                scanned = True
                #if(x) > 1420 - min_im_x:
                #    pass
                #else:
                cropped_im.put_pixel(x,y,(0,255,0),False)
            return scanned


        for dx in range(30):
            for dy in range(60):
                test_p3 = [-2.3 + 2.8 * dx/30, 0, 5.9 * dy/60]
                test_p2 = persp_proj( test_p3, player_rot)
                if test_p2[0] < 0 or test_p2[1] < 0:
                    continue
                try:
                    cropped_im.put_pixel(*test_p2, (255,255,0))
                except IndexError:
                    pass
        '''
        soft_line, soft_far_p3, soft_near_p3 = gen_line(-10)
        soft_far_p3 = soft_far_p3 or far_p3
        start_pos_x = soft_near_p3[0]
        delta_x = 0.1
        #print('DIST',start_pos_x, delta_x)
        while scan_pos(soft_far_p3, soft_near_p3, delta_x):
            delta_x += 0.1
            #print('deltax',delta_x)
        
        tp1 = persp_proj((x_right, water_height, 2), player_rot)
        tp2 = persp_proj((x_right, water_height, 3), player_rot)
        tp3 = persp_proj((x_right, water_height, 4), player_rot)
        
        tp4 = persp_proj( (far_p3[0], far_p3[1], far_p3[2] + 0.2), player_rot)
        tp5 = persp_proj( (far_p3[0], far_p3[1], far_p3[2] - 0.2), player_rot)
        
        tp6 = persp_proj([x_right,0,2], player_rot)
        tp7 = persp_proj([x_right,0,4], player_rot)
        rightline = Line( (tp6[0]-min_im_x, tp6[1]-min_im_y),  (tp7[0]-min_im_x, tp7[1]-min_im_y) )
        rightiter = rightline.get_iter(8, 0, max_im_x - min_im_x, 0, max_im_y - min_im_y)
        for x,y in rightiter:
            cropped_im.put_pixel(x,y,(0,0,255),False)

        tp6 = persp_proj([x_ops,0,2], player_rot)
        tp7 = persp_proj([x_ops,0,4], player_rot)
        rightline = Line( (tp6[0]-min_im_x, tp6[1]-min_im_y),  (tp7[0]-min_im_x, tp7[1]-min_im_y) )
        rightiter = rightline.get_iter(8, 0, max_im_x - min_im_x, 0, max_im_y - min_im_y)
        for x,y in rightiter:
            cropped_im.put_pixel(x,y,(0,0,255),False)

        tp6 = persp_proj([x_ops,0,5.9], player_rot)
        tp7 = persp_proj([x_right,0,5.9], player_rot)
        rightline = Line( (tp6[0]-min_im_x, tp6[1]-min_im_y),  (tp7[0]-min_im_x, tp7[1]-min_im_y) )
        rightiter = rightline.get_iter(8, 0, max_im_x - min_im_x, 0, max_im_y - min_im_y)
        for x,y in rightiter:
            cropped_im.put_pixel(x,y,(0,0,255),False)


        try:
            cropped_im.put_pixel(*tp1, (0,0,255))
            cropped_im.put_pixel(tp1[0] - 1, tp1[1]-1, (0,0,255))
            cropped_im.put_pixel(*tp2, (0,0,255))
            cropped_im.put_pixel(tp2[0] - 1, tp2[1]-1, (0,0,255))
            cropped_im.put_pixel(*tp3, (0,0,255))
            cropped_im.put_pixel(tp3[0] - 1, tp3[1]-1, (0,0,255))
        except IndexError:
            pass
        try:
            cropped_im.put_pixel(tp4[0] + 0, tp4[1]+0, (0,0,255))
            cropped_im.put_pixel(tp4[0] + 1, tp4[1]+0, (0,0,255))
            cropped_im.put_pixel(tp4[0] + 0, tp4[1]+1, (255,0,0))
            cropped_im.put_pixel(tp4[0] + 1, tp4[1]+1, (255,0,0))

            cropped_im.put_pixel(tp5[0] + 0, tp5[1]+0, (0,0,255))
            cropped_im.put_pixel(tp5[0] + 1, tp5[1]+0, (0,0,255))
            cropped_im.put_pixel(tp5[0] + 0, tp5[1]+1, (255,0,0))
            cropped_im.put_pixel(tp5[0] + 1, tp5[1]+1, (255,0,0))
        except IndexError:
            pass

        scan_ready = self.angle_correction_time == None or cap_time < self.angle_correction_time
        if scan_ready or self.last_angle_result != 'LEFT':
            hard_line, hard_far_p3, hard_near_p3 = gen_line(4, max_dist=3.5)
            hits_hard = scan_line(hard_line, crop=True)
            if hits_hard:
                if move:
                    self.rotate_to(MIN_ROT,0,0.64)
                self.last_angle_result = 'LEFT'
                self.angle_correction_time = cap_time + 1.5
                scan_ready = False

        if scan_ready:   
            if self.mouse.play_thread == None or not self.mouse.play_thread.is_alive():
                hits_soft = scan_line(soft_line, crop=False, dbgcol1=(140,20,20), dbgcol2=(20,20,140))
                if hits_soft:
                    if move:
                        self.rotate_to( m.degrees(player_rot[1])+20.5 - 10, m.degrees(player_rot[0]), 0.6)
                    self.last_angle_result = 'SOFTLEFT'
                    self.angle_correction_time = cap_time + 1.5
                elif self.last_angle_result != 'RIGHT':
                    if move:
                        self.rotate_to(MAX_ROT, 0, 3)
                    self.last_angle_result = 'RIGHT'
                    self.angle_correction_time = None
        #scan_dist(1.5,soft_far_p3, soft_near_p3)
        #scan_dist(3,soft_far_p3, soft_near_p3)
        '''


        return cropped_im, cap_time, after_cap_time

    def angle_test(self, sct,
        rotx=0, roty=0, camx=0, camy=0, camz=0, sens = 1,
        intrx=0, intry=0, intrz=0, intrsx=0, intrsy=0,
        inrslx=0, inrsly=0):
        t.sleep(0.1)
        debug = True
        
        vx = self.mouse.vx.value
        vy = self.mouse.vy.value
        player_rot = (
            m.radians(vy / SENSITIVITY / sens) +  m.radians(20) + m.radians(intrsy),  # m.radians(20  +roty),
            m.radians(vx / SENSITIVITY / sens)  -  m.radians(21.5) + m.radians(intrsx), # m.radians(21.5+rotx),
            0)#,0)

        ''' 
        |\ |
        | \|p-50
        '''
        far_rot = player_rot[1] - m.radians(30)
        #print('far rpt', far_rot)
        x_ops = -2.3
        #print('or zadj',-x_ops / max(m.tan(far_rot), 0.01))
        z_adj = x_ops / min(m.tan(far_rot), -0.01)
        #print('zadk',z_adj)
        z_adj = min(z_adj, 6.5)
        x_right = 0.35

        far_p3_max = [x_ops, self.var['WATER_MAX'], z_adj]
        far_p3_min = [x_ops, self.var['WATER_MIN'], z_adj]
        far_p2_max = persp_proj(far_p3_max, player_rot)
        far_p2_min = persp_proj(far_p3_min, player_rot)

        min_im_x = min(far_p2_max[0], far_p2_min[0])
        min_im_y = min(far_p2_max[1], EVENT_GRAB_TL[1])
        max_im_x = EVENT_GRAB_BR[0]
        max_im_y = HOT_POS[1] - 2

        min_im_x = 0#100
        min_im_y = 0#1440 - 1000
        max_im_x = 2560#100 + 1850
        max_im_y = 1440#1440

        bbox = (min_im_x, min_im_y, max_im_x, max_im_y)
        cap_time = t.time()
        #print('bboxxxx',bbox, far_p2_max[0], far_p2_min[0], far_p3_max, far_p3_min)
        sct_im = sct.grab(bbox)
        #print('bbox',bbox)
        np_im = np.array(sct_im) 
        cropped_im = CroppedIm(np_im, min_im_x, min_im_y)
        dbg('grabbed image')
        after_cap_time = t.time()

        water_height_line = Line(
            (far_p2_min[0] - min_im_x, far_p2_min[1] - min_im_y),
            (far_p2_max[0] - min_im_x, far_p2_max[1] - min_im_y)
        )
        iter_dist = 0
        line_iter = water_height_line.get_iter(
            WATER_HEIGHT_SPEED,
            0,
            max_im_x - min_im_x,
            0,
            max_im_y - min_im_y)
        max_bright = 160 * self.brightness

        water_blue_min = self.water_blue_min()#need new wall col this is for line
        water_height = None
        far_p2 = None
        far_p3 = None
        for (x, y) in line_iter:
            #print('iter ', x,y)
            pxl = cropped_im.im[y][x]
            if dist((0,0,0), pxl) < max_bright:
                if water_height == None:
                    d_water = iter_dist / abs(line_iter.max-line_iter.min)
                    d_max = (self.var['WATER_MAX'] - self.var['WATER_MIN'])

                    far_p3 = [far_p3_min[i] * (1-d_water) + far_p3_max[i] * d_water for i in range(3)]
                    far_p2 = (x+min_im_x,y+min_im_y)
                    water_height = max(
                     d_water * d_max + self.var['WATER_MIN'] - 0.15,
                    self.var['WATER_MIN']
                    )
                    cropped_im.put_pixel(x,y, (255,255,255), False)
                else:
                    cropped_im.put_pixel(x,y, (255,255,255), False)
            else:
                cropped_im.put_pixel(x,y, (255,255,255), False)
            iter_dist += WATER_HEIGHT_SPEED
        
        if water_height == None:
            water_height = self.var['WATER_MAX']
            far_p2 = far_p2_max
            far_p3 = far_p3_max
        
        water_height = 0
        
        im_tl = (min_im_x, min_im_y)
        im_sz = 0, max_im_x-min_im_x, 0, max_im_y-min_im_y
        lamp_left_p3 = (0,0.33,0.7)
        lamp_right_p3 = (0.5,0.33,1.4)
        lamp_left_p2 = persp_proj(lamp_left_p3, player_rot)
        lamp_right_p2 = persp_proj(lamp_right_p3, player_rot)

        lamp_left_p2 = ml(lamp_left_p2, im_tl)
        lamp_right_p2 = ml(lamp_right_p2,im_tl)

        lamp_line = Line(lamp_left_p2, lamp_right_p2)
        lamp_iter = lamp_line.get_iter(8, *im_sz)

        rod_top_p2 = 1420-min_im_x,740-min_im_y
        rod_bot_p2 = 1555-min_im_x,1440-1-min_im_y
        rod_line = Line(rod_bot_p2, rod_top_p2)

        pulling_rod_top_p2 = 1400-min_im_x,400-min_im_y
        pulling_rod_bot_p2 = 1770-min_im_x, 1440-1-min_im_y
        pulling_rod_line = Line(pulling_rod_top_p2, pulling_rod_bot_p2)

        above_rod_top_p2 = 1505-min_im_x,707-min_im_y
        above_rod_bot_p2 = 1677-min_im_x,1440-min_im_y
        above_rod_line = Line(above_rod_top_p2, above_rod_bot_p2)
        is_pulling = True
        for x,y in rod_line.get_iter(5,0,max_im_x-min_im_x, 0, max_im_y-min_im_y):
            pass#cropped_im.put_pixel(x,y,(0,0,0),False)


        for x,y in above_rod_line.get_iter(5,0,max_im_x-min_im_x, 0, max_im_y-min_im_y):
            pass#cropped_im.put_pixel(x,y,(0,0,0),False)
        pnt = None
        bobber_p3 = None

        cropped_im.put_pixel(2560//2,1440//2, (255,0,255))
        cropped_im.put_pixel(2560//2+1,1440//2+1, (255,255,255))
        cropped_im.put_pixel(2560//2,1440//2+1, (255,255,255))
        cropped_im.put_pixel(2560//2-1,1440//2, (255,255,255))
        cropped_im.put_pixel(2560//2,1440//2-1, (255,255,255))

        def scan_tri(p3_from, p3_top, p3_bot, scans, dir = 1, start=0, end=None):
            nonlocal pnt
            if type(end) == type(None):
                end = scans
            
            for i in range(start, end, dir):
                ch = i / scans
                scan_far_p3 = [
                    p3_from[j] * (1-ch) + p3_top[j] * ch for j in range(3)
                ]
                # image.png
                scan_near_p3 = [
                    p3_from[j] * (1-ch) + p3_bot[j] * ch for j in range(3)
                ]
                
                scan_dist = dist(scan_far_p3, scan_near_p3)
                #points = m.ceil(scan_dist / 0.1)
                scan_far_p2 = persp_proj(scan_far_p3, player_rot)
                scan_near_p2 = persp_proj(scan_near_p3, player_rot)
                scan_far_p2 = ml(scan_far_p2, im_tl)
                scan_near_p2 = ml(scan_near_p2, im_tl)
                

                line = Line(scan_near_p2, scan_far_p2)
                #print(scan_near_p2,scan_far_p2)
                

                if dir == -1:
                    x_, y_ = line_intersection(line, lamp_line)
                    used_max_y = min(max_im_y-min_im_y, m.floor(y_))
                else:
                    used_max_y = max_im_y-min_im_y
                used_max_y = max_im_y-min_im_y

                if is_pulling:
                    rot_x, rod_y = line_intersection(line, pulling_rod_line)
                else:
                    rot_x, rod_y = line_intersection(line, rod_line)

                #if rod_y > 0:
                #    used_max_y = min(used_max_y, m.floor(rod_y))
                #print('usedmaxyu',used_max_y)
                line_iter = line.get_iter(3, 0, max_im_x-min_im_x, 0, used_max_y   )
                
                for x,y in line_iter:
                    if y >= HOT_POS[1]-min_im_y: #HOT_POS[0]-min_im_x - 3 <= x <= HOT_POS[0] + 6 * SLOT_SIZE-min_im_x - 4 and
                        continue
                    #print('aaaaaa',y,x)
                    #print(cropped_im.im[y][x])
                    if water_blue_min < cropped_im.im[y][x][0]:
                        cropped_im.put_pixel(x,y,(0,255,255), False)
                    else:
                        if 1:
                            pnt = x,y
                            #(0.3490658503988659, -0.3752457891787809, 0)

                            rot_adj = (SCREEN_SIZE[0] // 2) / m.tan(m.radians(61 + inrsly))
                            rot_adjx = (SCREEN_SIZE[0] // 2) / m.tan(m.radians(61 + inrslx))

                            dx = (x + min_im_x - (SCREEN_SIZE[0] // 2))
                            mx = m.atan( dx / rot_adjx )
                            #mx =  mx / m.cos(mx) / m.cos(mx) * 2
                            dy = (y + min_im_y - (SCREEN_SIZE[1] // 2))
                            my = m.atan( dy / rot_adj )
                            #my = 2 * my * m.cos(my)* m.cos(my)
                            
                            pnt_rot = (
                                player_rot[0] + my + m.radians(roty),#, #*m.cos(mx)
                                player_rot[1] + mx + m.radians(rotx),#/ m.cos(my)*2 , #/m.cos(my)
                                0,
                            )
                            
                            if m.tan(pnt_rot[0]) == 0:
                                continue
                            incp_x = 1.53 / m.tan(pnt_rot[0]) * m.sin(pnt_rot[1])# - 0.09
                            incp_y = 0
                            incp_z = 1.53 / m.tan(pnt_rot[0]) * m.cos(pnt_rot[1])#   + 0.19

                            
                            #intersect_rot = rot_point((0,0,1), -pnt_rot[0], -pnt_rot[1])

                            '''intersect_line_p1 = (-0.09+intrx,1.53+intry,0.19+intrz)
                            intersect_line_p2 = (
                                -0.09 + intrx + m.sin(pnt_rot[1] + m.radians(intrsy)) * m.cos(pnt_rot[0]+ m.radians(intrsx)),
                                1.53 + intry - m.sin(pnt_rot[0]+ m.radians(intrsx))  ,
                                0.19 + intrz + m.cos(pnt_rot[1] + m.radians(intrsy)) * m.cos(pnt_rot[0] + m.radians(intrsx)),
                                )'''

                            #intersect_line_p1 = (-0.09,1.53,0.19)
                            #intersect_line_p2 = al(intersect_line_p1, intersect_rot)


                            '''#dbln = 20
                            for dbi in range(1,dbln):
                                dbpnt = [ intersect_line_p1[dbj] * (1-dbi/dbln) + intersect_line_p2[dbj] * dbi/dbln for dbj in range(3) ]
                                db2d = persp_proj(dbpnt, player_rot)
                                #print('db',dbpnt, db2d)
                                try:
                                    cropped_im.put_pixel(*db2d, (0,5,250))
                                except IndexError:
                                    pass

                            plane_p1 = (0, 0, 0)#(0, water_height, 0)
                            plane_dir = (0,1,0)

                            intersect_pnt = line_plane_intersection(intersect_line_p1, intersect_line_p2, plane_p1, plane_dir)
                            intersect_pnt = [intersect_pnt[0] + camx, intersect_pnt[1] + camy, intersect_pnt[2] + camz]
                            
                            intersect_pnt=[incp_x,incp_y,incp_z]
                            intersect_pnt_p2 = persp_proj(intersect_pnt, player_rot)

                            intersect_pntdbg = line_plane_intersection(
                                (-0.09, 1.53, 0.19),
                                 (-0.4908167452413109, 1.2499637299046151, 1.0623105090306013),
                                plane_p1,
                                plane_dir)

                            #intersect_pnt_p222 = intersect_pnt_p2[:]

                            #inter_x = round((intersect_pnt_p2[0] - SCREEN_SIZE[0]//2) / m.cos(pnt_rot[0]))
                            #inter_x = round(intersect_pnt_p2[0] - SCREEN_SIZE[0]//2)
                            #inter_y = (intersect_pnt_p2[1] - SCREEN_SIZE[1]//2)
                            #inter_dy = inter_y - inter_y / m.cos( m.pi * (inter_x) / 2560  )
                            #print('YMODDDDDDDD', inter_y, m.cos( m.pi * (inter_x) / 2560  ),  inter_x)
                            #inter_y = inter_y * m.cos( m.pi * (inter_x) / 2560  )'''
                            
                            #inter_y += inter_dy
                            '''intersect_pnt_p2 = (
                                inter_x  + SCREEN_SIZE[0]//2, # + SCREEN_SIZE[0]//2,
                                round(inter_y) + SCREEN_SIZE[1]//2
                            )'''

                            plane_p1 = (0, 0, 0)#(0, water_height, 0)
                            plane_dir = (0,1,0)


                            #print('pnt_rot',pnt_rot)
                            #print('points',intersect_line_p1, intersect_line_p2)
                            #isect2 = persp_proj(intersect_line_p2, player_rot)
                            '''print('isectdbg',isect2)
                            for i_ in range(-2,3):
                                for j_ in range(-2,3):
                                    if i_ + j_ % 2 == 0:
                                        cropped_im.put_pixel(
                                            isect2[0]+i_,
                                            isect2[1]+j_,
                                            (255,0,0)
                                        )
                                    else:
                                        cropped_im.put_pixel(
                                            isect2[0]+i_,
                                            isect2[1]+j_,
                                            (0,0,255)
                                        )'''

                            #print('dydx',dy,dx,m.degrees(my),m.degrees(mx) , 'pnt',pnt_rot)
                            #print('plane',plane_p1, plane_dir)
                            #print('intesect_pnt', intersect_pnt, intersect_pnt_p2)

                            #inter_y222 = inter_y * m.cos( m.pi * (inter_x) / 2560  )
                            
                            #inter_y += inter_dy
                            intersect_pnt = (incp_x, incp_y, incp_z)
                            intersect_pnt_p2 = persp_proj(intersect_pnt, player_rot) # player=(0,1.53,0)
                            '''intersect_pnt_p2 = [
                                round((intersect_pnt_p2[0] - SCREEN_SIZE[0]//2)/0.55/m.cos(2*my) + SCREEN_SIZE[0]//2),
                                round((intersect_pnt_p2[1] - SCREEN_SIZE[1]//2)/0.55 + SCREEN_SIZE[1]//2),
                            ]'''
                            intersect_pnt_p2 = [
                                round((intersect_pnt_p2[0] - SCREEN_SIZE[0]//2) + SCREEN_SIZE[0]//2),
                                round((intersect_pnt_p2[1] - SCREEN_SIZE[1]//2) + SCREEN_SIZE[1]//2),
                            ]

                            if cropped_im.im[y][x][0] == 0:
                                print('pnt',intersect_pnt,intersect_pnt_p2,'deg',mx,my,'player',player_rot)

                            #print('test', intersect_pnt,intersect_pnt_p2)
                            try:
                                for i_ in range(-2,3):
                                    for j_ in range(-2,3):
                                        if i_ + j_ % 2 == 1:
                                            cropped_im.put_pixel(
                                                intersect_pnt_p2[0]+i_,
                                                intersect_pnt_p2[1]+j_,
                                                (0,255,255)
                                            )

                                cropped_im.put_pixel(*intersect_pnt_p2, (0,0,255))
                                cropped_im.put_pixel(intersect_pnt_p2[0],intersect_pnt_p2[1]+1 , (0,0,255))
                                cropped_im.put_pixel(intersect_pnt_p2[0]+1,intersect_pnt_p2[1]+1 , (0,0,255))
                                cropped_im.put_pixel(intersect_pnt_p2[0]+1,intersect_pnt_p2[1] , (0,0,255))
                                cropped_im.put_pixel(*intersect_pnt_p2, (0,0,255))
                                cropped_im.put_pixel(intersect_pnt_p2[0],intersect_pnt_p2[1]+1 , (255,0,25))
                                cropped_im.put_pixel(intersect_pnt_p2[0]+2,intersect_pnt_p2[1]+1 , (255,0,25))
                                cropped_im.put_pixel(intersect_pnt_p2[0]+2,intersect_pnt_p2[1] , (255,0,25))

                                '''cropped_im.put_pixel(*intersect_pnt_p222, (0,0,255))
                                cropped_im.put_pixel(intersect_pnt_p222[0],intersect_pnt_p222[1]+1 , (0,0,255))
                                cropped_im.put_pixel(intersect_pnt_p222[0]+1,intersect_pnt_p222[1]+1 , (0,0,255))
                                '''
                            except Exception as e:
                                pass
                                #print('ERRR')
                                #print(e)
                            ratio = (scan_far_p2[1] - y) / (scan_far_p2[1] - scan_near_p2[1])
                            #print('ratio',ratio)
                            pos = [ scan_near_p3[i]*ratio + scan_far_p3[i]*(1-ratio) for i in range(3)]

                            bobber_p3 = pos

                            bobber_p2 = persp_proj(bobber_p3, player_rot)
                            #cropped_im.put_pixel(bobber_p2[0], bobber_p2[1], (250,0,0))
                            #cropped_im.put_pixel(bobber_p2[0]+1, bobber_p2[1], (250,0,0))
                            #cropped_im.put_pixel(bobber_p2[0], bobber_p2[1]+1, (250,0,0))
                            #cropped_im.put_pixel(bobber_p2[0], bobber_p2[1]-1, (250,0,0))
                            #cropped_im.put_pixel(bobber_p2[0]-1, bobber_p2[1], (250,0,0))

                        cropped_im.put_pixel(x,y,(255,255,0), False)
                if pnt == None and not is_pulling:                
                    above_rod_x, above_rod_y = line_intersection(line,above_rod_line)
                    print('abverrr',above_rod_x, scan_far_p2, scan_near_p2)
                    if above_rod_x < scan_far_p2[0]:
                        line_iter = line.get_iter(3,above_rod_x, max_im_x - min_im_x, 0, max_im_y - min_im_y)
                        for x,y in line_iter:
                            #print('aaaaaa',y,x)
                            #print(cropped_im.im[y][x])

                            x = round(x)
                            y = round(y)
                            if water_blue_min < cropped_im.im[y][x][0]:
                                cropped_im.put_pixel(x,y,(0,255,255), False)
                            else:
                                cropped_im.put_pixel(x,y,(255,255,0), False)
                
            if pnt:
                cropped_im.put_pixel(pnt[0],pnt[1],(255,255,255), False)
                cropped_im.put_pixel(pnt[0]+1,pnt[1],(255,255,255), False)
                cropped_im.put_pixel(pnt[0],pnt[1]-1,(255,255,255), False)
                cropped_im.put_pixel(pnt[0]+1,pnt[1]-1,(255,255,255), False)

        def scan_cube(scans, tl, br):
            for dy in range(scans):
                ch = dy / scans
                height = 0
                left_p3 = tl[0], height, br[2] * (1-ch) + tl[2] * ch
                right_p3 = br[0], height, br[2] * (1-ch) + tl[2] * ch
                left_p2 = persp_proj(left_p3, player_rot, (-0.04+camx,1.58+camy,0.19+camz))
                right_p2 = persp_proj(right_p3, player_rot, (-0.04+camx,1.58+camy,0.19+camz))
                line = Line(left_p2,right_p2)
                line_iter = line(3, min_im_x, max_im_x, min_im_y, max_im_y)
                for x,y in line_iter:
                    cropped_im.put_pixel(x,y,(0,255,255))
        

        for x, y in lamp_iter:
            cropped_im.put_pixel(x,y,(255,255,0), False)

        '''scan_tri(
            (-2.3,water_height,0.3), (-2.3,water_height,5.8), (-2.3+2.75,water_height,0.3),
            40, 1, 3, 40
            )
        scan_tri(
            (-2.3+2.75,water_height,5.8), (-2.3+2.75,water_height,0.3), (-2.3,water_height,5.8), 
            40, -1, 40, 1
            )'''
        scan_tri(
        (-2.3,0,0.3), (-2.3,0,5.8), (-2.3+2.75,0,0.3),
            20, 1, 1, 20
            )
        scan_tri(
            (-2.3+2.75,0,5.8), (-2.3+2.75,0,0.3), (-2.3,0,5.8), 
            20, -1, 20, 1
            )

        #scan_tri(16, (-2.3,-3,0.3), (-2.3,-3,5.8), (-2.3+2.8,-3,0.3) )
        #scan_tri(16, (-2.3+2.8,-3,5.8), (-2.3+2.8,-3,0.3), (-2.3,-3,5.8) , -1 )


        return cropped_im, cap_time, player_rot, bobber_p3

    def angle_test22(self, sct,
        rotx=0, roty=0, camx=0, camy=0, camz=0, sens = 1,
        intrx=0, intry=0, intrz=0, intrsx=0, intrsy=0,
        inrslx=0, inrsly=0):
        t.sleep(0.1)
        debug = True
        
        player_rot = (
            m.radians(20) + m.radians(intrsy),  # m.radians(20  +roty),
            -m.radians(21.5) + m.radians(intrsx), # m.radians(21.5+rotx),
            0)

        min_im_x = 0#100
        min_im_y = 0#1440 - 1000
        max_im_x = 2560#100 + 1850
        max_im_y = 1440#1440

        bbox = (min_im_x, min_im_y, max_im_x, max_im_y)
        cap_time = t.time()
        #print('bboxxxx',bbox, far_p2_max[0], far_p2_min[0], far_p3_max, far_p3_min)
        sct_im = sct.grab(bbox)
        #print('bbox',bbox)
        np_im = np.array(sct_im) 
        cropped_im = CroppedIm(np_im, min_im_x, min_im_y)
        dbg('grabbed image')

        water_height = 0
        
        pnt = None

        cropped_im.put_pixel(2560//2,1440//2, (255,0,255))
        cropped_im.put_pixel(2560//2+1,1440//2+1, (255,255,255))
        cropped_im.put_pixel(2560//2,1440//2+1, (255,255,255))
        cropped_im.put_pixel(2560//2-1,1440//2, (255,255,255))
        cropped_im.put_pixel(2560//2,1440//2-1, (255,255,255))
        im_tl = min_im_x,min_im_y
        def scan_tri(p3_from, p3_top, p3_bot, scans, dir = 1, start=0, end=None):
            nonlocal pnt
            if type(end) == type(None):
                end = scans
            
            for i in range(start, end, dir):
                ch = i / scans
                scan_far_p3 = [
                    p3_from[j] * (1-ch) + p3_top[j] * ch for j in range(3)
                ]
                # image.png
                scan_near_p3 = [
                    p3_from[j] * (1-ch) + p3_bot[j] * ch for j in range(3)
                ]
                
                scan_far_p2 = persp_proj(scan_far_p3, player_rot)
                scan_near_p2 = persp_proj(scan_near_p3, player_rot)
                scan_far_p2 = ml(scan_far_p2, im_tl)
                scan_near_p2 = ml(scan_near_p2, im_tl)
                

                line = Line(scan_near_p2, scan_far_p2)
                #print(scan_near_p2,scan_far_p2)
                

                used_max_y = max_im_y-min_im_y

                line_iter = line.get_iter(3, 0, max_im_x-min_im_x, 0, used_max_y   )
                
                e_x = SCREEN_SIZE[0]/2
                e_y = SCREEN_SIZE[1]/2
                e_z = SCREEN_SIZE[1]/2 * 44/45

                for x,y in line_iter:
                    if y >= HOT_POS[1]-min_im_y: #HOT_POS[0]-min_im_x - 3 <= x <= HOT_POS[0] + 6 * SLOT_SIZE-min_im_x - 4 and
                        continue
                    #print('aaaaaa',y,x)
                    #print(cropped_im.im[y][x])
                    if 130 < cropped_im.im[y][x][0]:
                        cropped_im.put_pixel(x,y,(0,255,255), False)
                    else:
                        try:
                            pnt = x,y
                            #(0.3490658503988659, -0.3752457891787809, 0)
                            rot_adj = (SCREEN_SIZE[0] // 2) / m.tan(m.radians(61 + inrsly))
                            rot_adjx = (SCREEN_SIZE[0] // 2) / m.tan(m.radians(61 + inrslx))

                            dx = x + min_im_x
                            dy = y + min_im_y

                            intersect_pnt = persp_pnt(dx,dy,player_rot)
                            intersect_pnt_p2 = persp_proj(intersect_pnt, player_rot)

                            if cropped_im.im[y][x][0] == 0 and cropped_im.im[y][x][2] == 0:
                                print('pnt',x,y,'int',intersect_pnt,intersect_pnt_p2,'deg',dx,dy,'player',player_rot)

                            try:
                                for i_ in range(-2,3):
                                    for j_ in range(-2,3):
                                        if i_ + j_ % 2 == 1:
                                            cropped_im.put_pixel(
                                                intersect_pnt_p2[0]+i_,
                                                intersect_pnt_p2[1]+j_,
                                                (0,255,255)
                                            )

                            except Exception as e:
                                pass
                        except Exception as e:
                            print (e)

                        cropped_im.put_pixel(x,y,(255,255,0), False)
                
            if pnt:
                cropped_im.put_pixel(pnt[0],pnt[1],(255,255,255), False)
                cropped_im.put_pixel(pnt[0]+1,pnt[1],(255,255,255), False)
                cropped_im.put_pixel(pnt[0],pnt[1]-1,(255,255,255), False)
                cropped_im.put_pixel(pnt[0]+1,pnt[1]-1,(255,255,255), False)

        
        scan_tri(
            (-2.3,0,0.3), (-2.3,0,5.8), (-2.3+2.75,0,0.3),
            20, 1, 1, 20
            )
        scan_tri(
            (-2.3+2.75,0,5.8), (-2.3+2.75,0,0.3), (-2.3,0,5.8), 
            20, -1, 20, 1
            )


        return cropped_im, cap_time, player_rot, None

    def get_water_height(self, cropped_im, player_rot):
        x_ops = -2.3
        z_adj = 3

        far_p3_max = [x_ops, self.var['WATER_MAX'], z_adj]
        far_p3_min = [x_ops, self.var['WATER_MIN'], z_adj]
        far_p2_max = persp_proj(far_p3_max, player_rot)
        far_p2_min = persp_proj(far_p3_min, player_rot)
        water_height_line = Line(
            (far_p2_min[0] - cropped_im.left, far_p2_min[1] - cropped_im.top),
            (far_p2_max[0] - cropped_im.left, far_p2_max[1] - cropped_im.top)
        )
        iter_dist = 0
        line_iter = water_height_line.get_iter(
            WATER_HEIGHT_SPEED,
            0,
            max_im_x - min_im_x,
            0,
            max_im_y - min_im_y)
        max_bright = 160 * self.brightness

        water_blue_min = self.water_blue_min()#need new wall col this is for line
        water_height = None
        far_p2 = None
        far_p3 = None
        for (x, y) in line_iter:
            #print('iter ', x,y)
            pxl = cropped_im.im[y][x]
            if dist((0,0,0), pxl) < max_bright:
                if water_height == None:
                    d_water = iter_dist / abs(line_iter.max-line_iter.min)
                    d_max = (self.var['WATER_MAX'] - self.var['WATER_MIN'])

                    far_p3 = [far_p3_min[i] * (1-d_water) + far_p3_max[i] * d_water for i in range(3)]
                    far_p2 = (x+min_im_x,y+min_im_y)
                    water_height = max(
                     d_water * d_max + self.var['WATER_MIN'] - 0.15,
                    self.var['WATER_MIN']
                    )
                    cropped_im.put_pixel(x,y, (255,255,255), False)
                else:
                    cropped_im.put_pixel(x,y, (255,255,255), False)
            else:
                cropped_im.put_pixel(x,y, (255,255,255), False)
            iter_dist += WATER_HEIGHT_SPEED
        
        if water_height == None:
            water_height = self.var['WATER_MAX']
        return water_height

    def get_bobber_pos(self,sct):
        min_im_x = 0
        max_im_x = SCREEN_SIZE[0]
        min_im_y = 0
        max_im_y = SCREEN_SIZE[1]
        
        bbox = (min_im_x, min_im_y, max_im_x, max_im_y)
        im_tl = min_im_x, min_im_y

        vx = self.mouse.vx.value
        vy = self.mouse.vy.value
        cap_time = t.time()
        sct_im = sct.grab(bbox)
        np_im = np.array(sct_im) 
        cropped_im = CroppedIm(np_im, min_im_x, min_im_y)
        player_rot = (
            m.radians(vy / SENSITIVITY) +  m.radians(20),
            m.radians(vx / SENSITIVITY)  -  m.radians(21.5),
            0)
        x_ops = -2.3
        z_adj = 3

        far_p3_max = [x_ops, self.var['WATER_MAX'], z_adj]
        far_p3_min = [x_ops, self.var['WATER_MIN'], z_adj]
        far_p2_max = persp_proj(far_p3_max, player_rot)
        far_p2_min = persp_proj(far_p3_min, player_rot)
        water_height_line = Line(
            (far_p2_min[0] - min_im_x, far_p2_min[1] - min_im_y),
            (far_p2_max[0] - min_im_x, far_p2_max[1] - min_im_y)
        )
        iter_dist = 0
        line_iter = water_height_line.get_iter(
            WATER_HEIGHT_SPEED,
            0,
            max_im_x - min_im_x,
            0,
            max_im_y - min_im_y)
        max_bright = 160 * self.brightness

        water_blue_min = self.water_blue_min()#need new wall col this is for line
        water_height = None
        far_p2 = None
        far_p3 = None
        for (x, y) in line_iter:
            #print('iter ', x,y)
            pxl = cropped_im.im[y][x]
            if dist((0,0,0), pxl) < max_bright:
                if water_height == None:
                    d_water = iter_dist / abs(line_iter.max-line_iter.min)
                    d_max = (self.var['WATER_MAX'] - self.var['WATER_MIN'])

                    far_p3 = [far_p3_min[i] * (1-d_water) + far_p3_max[i] * d_water for i in range(3)]
                    far_p2 = (x+min_im_x,y+min_im_y)
                    water_height = max(
                     d_water * d_max + self.var['WATER_MIN'] - 0.15,
                    self.var['WATER_MIN']
                    )
                    cropped_im.put_pixel(x,y, (255,255,255), False)
                else:
                    cropped_im.put_pixel(x,y, (255,255,255), False)
            else:
                cropped_im.put_pixel(x,y, (255,255,255), False)
            iter_dist += WATER_HEIGHT_SPEED
        
        if water_height == None:
            water_height = self.var['WATER_MAX']
            far_p2 = far_p2_max
            far_p3 = far_p3_max


        im_tl = (min_im_x, min_im_y)
        im_sz = 0, max_im_x-min_im_x, 0, max_im_y-min_im_y
        lamp_left_p3 = (0,0.33,0.7)
        lamp_right_p3 = (0.5,0.33,1.4)
        lamp_left_p2 = persp_proj(lamp_left_p3, player_rot)
        lamp_right_p2 = persp_proj(lamp_right_p3, player_rot)

        lamp_left_p2 = ml(lamp_left_p2, im_tl)
        lamp_right_p2 = ml(lamp_right_p2,im_tl)

        lamp_line = Line(lamp_left_p2, lamp_right_p2)
        lamp_iter = lamp_line.get_iter(8, *im_sz)

        rod_top_p2 = 1420-min_im_x,740-min_im_y
        rod_bot_p2 = 1555-min_im_x,1440-1-min_im_y
        rod_line = Line(rod_bot_p2, rod_top_p2)

        pulling_rod_top_p2 = 1400-min_im_x,400-min_im_y
        pulling_rod_bot_p2 = 1770-min_im_x, 1440-1-min_im_y
        pulling_rod_line = Line(pulling_rod_top_p2, pulling_rod_bot_p2)

        above_rod_top_p2 = 1505-min_im_x,707-min_im_y
        above_rod_bot_p2 = 1677-min_im_x,1440-min_im_y
        above_rod_line = Line(above_rod_top_p2, above_rod_bot_p2)
        is_pulling = True
        for x,y in rod_line.get_iter(5,0,max_im_x-min_im_x, 0, max_im_y-min_im_y):
            pass#cropped_im.put_pixel(x,y,(0,0,0),False)


        for x,y in above_rod_line.get_iter(5,0,max_im_x-min_im_x, 0, max_im_y-min_im_y):
            pass

        def scan_tri(p3_from, p3_top, p3_bot, scans, start, end):
            if start < end:
                dir = 1
            else:
                dir = -1
            for i in range(start, end, dir):
                ch = i / scans
                scan_far_p3 = [
                    p3_from[j] * (1-ch) + p3_top[j] * ch for j in range(3)
                ]
                scan_near_p3 = [
                    p3_from[j] * (1-ch) + p3_bot[j] * ch for j in range(3)
                ]

                
                scan_far_p2 = persp_proj(scan_far_p3, player_rot)
                scan_near_p2 = persp_proj(scan_near_p3, player_rot)
                scan_far_p2 = ml(scan_far_p2, im_tl)
                scan_near_p2 = ml(scan_near_p2, im_tl)
                line = Line(scan_near_p2, scan_far_p2)


        def scan_tri(p3_from, p3_top, p3_bot, scans, dir = 1, start=0, end=None):
            if type(end) == type(None):
                end = scans
            
            for i in range(start, end, dir):
                ch = i / scans
                scan_far_p3 = [
                    p3_from[j] * (1-ch) + p3_top[j] * ch for j in range(3)
                ]
                # image.png
                scan_near_p3 = [
                    p3_from[j] * (1-ch) + p3_bot[j] * ch for j in range(3)
                ]
                
                scan_far_p2 = persp_proj(scan_far_p3, player_rot)
                scan_near_p2 = persp_proj(scan_near_p3, player_rot)
                scan_far_p2 = ml(scan_far_p2, im_tl)
                scan_near_p2 = ml(scan_near_p2, im_tl)
                

                line = Line(scan_near_p2, scan_far_p2)
                #print(scan_near_p2,scan_far_p2)
                

                used_max_y = max_im_y-min_im_y

                line_iter = line.get_iter(3, 0, max_im_x-min_im_x, 0, used_max_y   )
                
                e_x = SCREEN_SIZE[0]/2
                e_y = SCREEN_SIZE[1]/2
                e_z = SCREEN_SIZE[1]/2 * 44/45

                for x,y in line_iter:
                    if y >= HOT_POS[1]-min_im_y: #HOT_POS[0]-min_im_x - 3 <= x <= HOT_POS[0] + 6 * SLOT_SIZE-min_im_x - 4 and
                        continue
                    #print('aaaaaa',y,x)
                    #print(cropped_im.im[y][x])
                    if 130 < cropped_im.im[y][x][0]:
                        cropped_im.put_pixel(x,y,(0,255,255), False)
                    else:
                        try:
                            pnt = x,y
                            #(0.3490658503988659, -0.3752457891787809, 0)
                            rot_adj = (SCREEN_SIZE[0] // 2) / m.tan(m.radians(61 + inrsly))
                            rot_adjx = (SCREEN_SIZE[0] // 2) / m.tan(m.radians(61 + inrslx))

                            dx = x + min_im_x
                            dy = y + min_im_y

                            intersect_pnt = persp_pnt(dx,dy,player_rot)
                            intersect_pnt_p2 = persp_proj(intersect_pnt, player_rot)

                            if cropped_im.im[y][x][0] == 0 and cropped_im.im[y][x][2] == 0:
                                print('pnt',x,y,'int',intersect_pnt,intersect_pnt_p2,'deg',dx,dy,'player',player_rot)

                            try:
                                for i_ in range(-2,3):
                                    for j_ in range(-2,3):
                                        if i_ + j_ % 2 == 1:
                                            cropped_im.put_pixel(
                                                intersect_pnt_p2[0]+i_,
                                                intersect_pnt_p2[1]+j_,
                                                (0,255,255)
                                            )

                            except Exception as e:
                                pass
                        except Exception as e:
                            print (e)

                        cropped_im.put_pixel(x,y,(255,255,0), False)
                
            if pnt:
                cropped_im.put_pixel(pnt[0],pnt[1],(255,255,255), False)
                cropped_im.put_pixel(pnt[0]+1,pnt[1],(255,255,255), False)
                cropped_im.put_pixel(pnt[0],pnt[1]-1,(255,255,255), False)
                cropped_im.put_pixel(pnt[0]+1,pnt[1]-1,(255,255,255), False)

        
        scan_tri(
            (-2.3,0,0.3), (-2.3,0,5.8), (-2.3+2.75,0,0.3),
            20, 1, 1, 20
            )
        scan_tri(
            (-2.3+2.75,0,5.8), (-2.3+2.75,0,0.3), (-2.3,0,5.8), 
            20, -1, 20, 1
            )
        
    def test_fov(self):
        import tkinter as tk
        import cv2

        #rotx + 5
        '''
        rotx = 5
        roty = 9

        fox = 44

        camx = -0.08
        camy = 1.53
        camz = 
        '''

        new_press = False
        def pressed():
            nonlocal new_press
            new_press = True

        master = tk.Tk()
        w1 = tk.Scale(master, label='rotx', from_=-30, to=30, length=512, orient=tk.HORIZONTAL)
        w1.pack()
        w2 = tk.Scale(master, label='roty', from_=-30, to=30.0, length=512, orient=tk.HORIZONTAL)
        w2.pack()

        '''w_sensx = tk.Scale(master,label='sensx', from_=50, to=150, length=512, orient=tk.HORIZONTAL)
        w_sensx.pack()
        w_sensy = tk.Scale(master,label='sensy', from_=50, to=150, length=512, orient=tk.HORIZONTAL)
        w_sensy.pack()
        w_fov = tk.Scale(master,label='fov', from_=40, to=50, length=512, orient=tk.HORIZONTAL)
        w_fov.pack()'''
        w_sensy = tk.Scale(master,label='sens', from_=-50, to=50, length=512, orient=tk.HORIZONTAL)
        w_sensy.pack()

        w_camx = tk.Scale(master,label='camx', from_=-20, to=20, length=512, orient=tk.HORIZONTAL)
        w_camx.pack()
        w_camy = tk.Scale(master,label='camy', from_=-20, to=20, length=512, orient=tk.HORIZONTAL)
        w_camy.pack()
        w_camz = tk.Scale(master,label='camz', from_=-20, to=20, length=512, orient=tk.HORIZONTAL)
        w_camz.pack()

        #rx
        w_inrrx = tk.Scale(master,label='inrrx', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrrx.pack()
        w_inrry = tk.Scale(master,label='inrry', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrry.pack()
        w_inrrz = tk.Scale(master,label='intrrz', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrrz.pack()
        w_inrsx = tk.Scale(master,label='intrsx', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrsx.pack()
        w_inrsy = tk.Scale(master,label='intrsy', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrsy.pack()
        w_inrslx = tk.Scale(master,label='inrslx', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrslx.pack()
        w_inrsly = tk.Scale(master,label='inrsly', from_=-100, to=100.0, length=512, orient=tk.HORIZONTAL)
        w_inrsly.pack()

        #rx
        w3 = tk.Scale(master,label='movex', from_=-25, to=25.0, length=512, orient=tk.HORIZONTAL)
        w3.pack()
        w4 = tk.Scale(master,label='movey', from_=-25, to=25.0, length=512, orient=tk.HORIZONTAL)
        w4.pack()





        button = tk.Button(master, text ="rotate", command=pressed)
        button.pack()

        self.handle_pull(1)

        self.temp_heat_tracker = False
        self.temp_time = r.uniform(self.temp_min_time, self.temp_max_time)
        self.temp_stopped = True#False
        self.fishing_left = False
        debug = True#False# True
        self.last_angle_result = 'RIGHT'
        self.angle_correction_time = None

        self.band_positions = []
        self.last_pull_time = t.time()

        with mss.mss() as sct: 
            while True:
                #e = (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, SCREEN_SIZE[1] * w_fov.get() / 90 )
                #cropped, cap, after = self.angle_test(sct,False,w1.get(), w2.get(), w_sensx.get()/100, w_sensy.get()/100, e=e, camx=w_camx.get()/100, camy=w_camy.get()/100, camz=w_camz.get()/100)
                inf = self.angle_test22(sct,
                w1.get(), w2.get(),#rot
                
                w_camx.get()/100, w_camy.get()/100, w_camz.get()/100,
                
                1 + w_sensy.get() / 100,
                
                intrx=w_inrrx.get()/100,
                intry=w_inrry.get()/100,
                intrz=w_inrrz.get()/100,
                intrsx=w_inrsx.get(),
                intrsy=w_inrsy.get(),
                inrslx=w_inrslx.get(),
                inrsly=w_inrsly.get()
                
                ) #intrx=0, intry=0, intrz=0, intrsx=1, intrsy=1








                cropped = inf[0]
                master.update()
                cv2.imshow("test", cropped.im)
                if new_press:
                    print('ROTATE')
                    t.sleep(5)
                    self.rotate_to(w3.get(), w4.get())
                    self.mouse.play_thread.join()
                new_press = False






    def update_actions(self, last_action_time, force_stop=False):
        dbg('@update_actions')
        #print('update time', last_action_time)
        if self.cooling:
            dbg('cooling ' + str(self.heat) ,1)
            self.switch_keys([])
            self.heat -= last_action_time
            if self.heat <= 0:
                self.heats = []
                self.cooling = False
                self.temp_heat_tracker = False
                self.last_pull_time = t.time()

        if not self.cooling:
            self.heat += last_action_time
            desired = self.desired_keys()
            #acc = self.band_acceleration()
            heat_val = sum(self.heats) / max(0.7, len(self.heats))
            if heat_val > 75 or force_stop: #acc >= 630:
                #if self.temp_heat_tracker == False:
                #    self.temp_heat_tracker = True
                #    #if r.randint(0,2) < 0:
                #dbg('CHOSE REST',1)
                self.band_positions = []
                self.heats = []
                self.cooling = True
                self.heat = max(1, self.heat ** 0.75)
                self.switch_keys([])
                dbg('%update_actions wipe')
                return True
            else:
                self.switch_keys(desired)
        return False
        #dbg('%update_actions')

    def event_check(self, im=None):
        dbg('@event_check')
        is_array = False
        if type(im) == none_type:
            print('EVENT GRABBING')
            im = iGrab.grab()
        elif type(im) == CroppedIm:
            is_array = True

        line_blue_max = self.rod_blue_max()
        
        def rod_snapped():
            if is_array:
                for x in range(RAISED_ROD_TL[0] - im.left, RAISED_ROD_BR[0] - im.left, RAISED_ROD_SPEED):
                    for y in range(RAISED_ROD_TL[1] - im.top, RAISED_ROD_BR[1] - im.top, RAISED_ROD_SPEED):
                        px = im.im[y][x]
                        if px[0] <= line_blue_max:
                            print('snap at',x,y,px)
                            return 'SNAP'

            else:
                for x in range(RAISED_ROD_TL[0], RAISED_ROD_BR[0], RAISED_ROD_SPEED):
                    for y in range(RAISED_ROD_TL[1], RAISED_ROD_BR[1], RAISED_ROD_SPEED):
                        px = im.getpixel((x,y))
                        if px[2] <= line_blue_max:
                            return 'SNAP'
            #dbg('%event_check.rod_snapped -- nosapped')
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

        #dbg('& event - got pickup check')
        if got_pickup(im): # success
            dbg('! got pickup')
            im = iGrab.grab()
            other_rod = self.inactive_rod(im)
            if other_rod != None:
                print('select second rod')
                t.sleep(g(0,0.2))
                pressSlot(other_rod)
                t.sleep(g(0.3))
                #dbg('%event_check - fastsuccess')
                return 'FASTSUCCESS'
            else:
                #dbg('%event_check - success')
                return 'SUCCESS'
        #dbg('& event - check snap start')
        if self.brightness > 0.0:
            #print('NIGHT SNAP\n;lllllllllllllll\nlllllllllllll')
            ret =  rod_snapped()
        else:
            ret = rod_snapped_night()
        #dbg('%event_check - rodsnapped=' + str(ret))
        return ret

    def estimate_heat(self, time_change):
        #dbg('@estimate_heat',1)
        POINTS_LEN = 8
        if len(self.band_positions) <= POINTS_LEN or time_change < 0.7:
            #dbg('skip heat est',1)
            return -1
        '''
        new_heat = self.rod_heat_manager.thread_get()
        if new_heat:
            self.heats.append(new_heat)
            self.heats = self.heats[-1:]
        if self.rod_heat_manager.thread == None:
            data = [self.band_positions[-1][0] - 1760,self.band_positions[-1][1] - 880, time_change]
            for samp_ind in range(0, POINTS_LEN, 1):
                samp = self.band_positions[-2-samp_ind]
                next_samp = self.band_positions[-1-samp_ind]
                dx = next_samp[0] - samp[0]
                dy = next_samp[1] - samp[1]
                dt = next_samp[2] - samp[2]
                data.append(dx)
                data.append(dy)
                data.append(dt)
            #print('using data', data)
            self.rod_heat_manager.thread_predict(data)
        '''
        data = [self.band_positions[-1][0] - 1760,self.band_positions[-1][1] - 880, time_change]
        for samp_ind in range(0, POINTS_LEN, 1):
            samp = self.band_positions[-2-samp_ind]
            next_samp = self.band_positions[-1-samp_ind]
            dx = next_samp[0] - samp[0]
            dy = next_samp[1] - samp[1]
            dt = next_samp[2] - samp[2]
            data.append(dx)
            data.append(dy)
            data.append(dt)
        self.heats.append(self.rod_heat_manager.numpy_predict(data))
        self.heats = self.heats[-2:]
        #dbg('%estimate_heat',1)

    def handle_fight(self):
        dbg('@handle_fight')
        #t.sleep(3)
        #return 'TIMEOUT'
        self.temp_heat_tracker = False
        self.temp_time = r.uniform(self.temp_min_time, self.temp_max_time)
        self.temp_stopped = True#False
        self.fishing_left = False
        debug = True#False# True
        self.last_angle_result = 'RIGHT'

        with mss.mss() as sct:
            start_time = t.time()
            last_time = start_time
            new_time = start_time
            last_ims = []
            itersi = 0
            datas = []
            self.band_positions = []
            self.last_pull_time = t.time()
            #self.brightness = get_brightness(im)
            print('grabbing',(*EVENT_GRAB_TL, *EVENT_GRAB_BR))

            event_im = np.array(sct.grab((*EVENT_GRAB_TL, *EVENT_GRAB_BR)))
            cropped_im = CroppedIm(event_im, *EVENT_GRAB_TL)

            event = self.event_check(cropped_im)
            print('looping')
            times = [0,0,0,0,0,0,0,0,0,0]
            time_samples = 0
            while not event or new_time - start_time > self.var['MAXWAIT']:           
                last_time = new_time
                new_time = t.time()
                time_change = new_time - last_time
                new_times = []


                dbg('* fight loop -  last time change' +  str(time_change) + ' bright' + str(self.brightness) + ' heats' + str(self.heats), 1 )
                
                cropped_im, cap_time,after_cap_time = self.angle_test(sct) #handle_angle_correction
                new_times.append(cap_time)
                new_times.append(after_cap_time)
                new_times.append(t.time())
                event = self.event_check(cropped_im)
                new_times.append(t.time())
                new_pos = self.track_band(cropped_im, cap_time)
                #dbg('&fight - new pos' + str(new_pos), 1 )
                new_times.append(t.time())
                debug_data = {
                    'tm':new_time,
                    'im':cropped_im,
                }
                if new_pos:
                    debug_data['xy'] = new_pos[:2],
                    debug_data['sp'] = new_pos[3]

                
                new_times.append(t.time())

                if new_pos and not self.cooling:
                    self.estimate_heat(new_time-self.last_pull_time)
                    if debug and len(self.heats):
                        #print('HEAT ',heat_est)
                        try:
                            cropped_im.put_pixel(101,0, (255,255,0), False)
                            cropped_im.put_pixel(101,1, (255,255,0), False)
                            cropped_im.put_pixel(100,0, (255,255,0), False)
                            cropped_im.put_pixel(100,1, (255,255,0), False)

                            cropped_im.put_pixel(201,1, (255,255,0), False)
                            cropped_im.put_pixel(201,0, (255,255,0), False)
                            cropped_im.put_pixel(200,1, (255,255,0), False)
                            cropped_im.put_pixel(200,0, (255,255,0), False)

                            cropped_im.put_pixel(round(self.heats[-1])+101,0, (0,255,0), False)
                            cropped_im.put_pixel(round(self.heats[-1])+101,1, (0,255,0), False)
                            cropped_im.put_pixel(round(self.heats[-1])+100,0, (0,255,0), False)
                            cropped_im.put_pixel(round(self.heats[-1])+100,1, (0,255,0), False)
                        except Exception as e:
                            print('HEAT ERR', e)
                new_times.append(t.time())               

                #force_stop = False
                #if not self.temp_stopped and new_time - start_time > self.temp_time:
                #    self.temp_stopped = True
                #    force_stop = True
                force_stop = False
                wipe = self.update_actions(time_change, force_stop)

                if self.cooling:
                    debug_data['cl'] = True
                
                if wipe:
                    #last_ims = []
                    #datas = []
                    cropped_im.put_pixel(30,30,(255,0,0),offset=False)
                    cropped_im.put_pixel(31,30,(0,255,0),offset=False)
                    cropped_im.put_pixel(32,30,(0,0,255),offset=False)
                last_ims.append( cropped_im )
                #if itersi % 10 == 0:
                #    self.brightness = get_brightness(im)
                
                new_times.append(t.time())

                for i in range(len(new_times)-1):
                    times[i]+=new_times[i+1]-new_times[i]
                time_samples += 1

                datas.append(debug_data)
                #datas.append(self.band_acceleration())

                

                #last_ims = last_ims[-110:]
                #itersi += 1
                #if itersi % 1 == 0:
                    
                # #   print('iter time', time_change)
                #t.sleep(max(0,self.var['SCANTIME'] - time_change))
                #print('sleeping', max(0,self.var['SCANTIME'] - time_change))
        for i in range(len(times)):
            times[i] = times[i] / max(1,time_samples)
        
        print('times:', times)
        #event = 'SNAP'


        if debug and len(datas):
            name = str(start_time)[5:12]
            end_time = datas[-1]['tm']
            start_time = datas[0]['tm']
            #make_video([Image.fromarray(cim.im) for cim in last_ims], str(start_time)[6:12] + '.mp4')
            max_lx = 0
            min_lx = 9999
            max_rx = 0
            min_rx = 9999
            max_ty = 0
            min_ty = 9999
            min_by = 9999
            max_by = 0
            for data in datas:
                cim = data['im']
                min_lx = min(cim.left, min_lx)
                max_lx = max(cim.left, max_lx)
                max_ty = max(cim.top, max_ty)
                min_ty = min(cim.top, min_ty)
                #print('type', type(cim.im), type(cim.im.size), cim.im.size)
                max_rx = max(max_rx, cim.left + cim.im.shape[1])
                max_by = max(max_by, cim.left + cim.im.shape[0])
                min_rx = min(min_rx, cim.left + cim.im.shape[1])
                min_by = min(min_by, cim.left + cim.im.shape[0])
            fps = len(last_ims)/(end_time-start_time)
            sims = []
            for data in datas:
                cim = data['im']
                if end_time - 4.4 < data['tm']:
                    for y in range(0, 100, 3):
                        cim.put_pixel(0,y, (0,0,255), offset=False)
                        cim.put_pixel(1,y, (0,0,255), offset=False)

                if 'cl' in data.keys():
                    for y in range(0, 100, 3):
                        cim.put_pixel(2,y, (0,255,0), offset=False)
                        cim.put_pixel(3,y, (0,255,0), offset=False)

                pim = Image.fromarray(cim.im)
                newsize = 1#2
                if newsize != 1:
                    pim = pim.resize((
                        round(pim.size[0] /newsize),
                        round(pim.size[1]/newsize)
                        ))
                sim = Image.new('RGBA', (
                    round((max_rx - min_lx)/newsize),
                    round((max_by - min_ty)/newsize)
                    ), color=(0,0,0,255))

                sim.paste(pim, (
                    round((cim.left - min_lx)/newsize),
                    round((cim.top - min_ty)/newsize)
                    ))    
                #sim = sim.crop
                #sim = sim.crop((min_lx-cim.left, min_ty-cim.top, cim.size[0] + max_rx - (cim.left + cim.im.size[0])  ,  cim.size[1] + max_by - (cim.top + cim.im.size[1])  ))
                sims.append(sim)

            make_video(sims, name + '.mp4', fps=(round(fps  )))

        if debug and len(datas):
            name = str(start_time)[5:12]
            end_time = datas[-1]['tm']
            start_time = datas[0]['tm']
            if event == 'SNAP': 
                dbg('# save snap pics')
                for data in datas:
                    del data['im']
                with open('dbg\\snaps.txt', 'a+') as f:
                    f.write(json.dumps(( name, datas)) + '\n')
                

            elif event:
                for data in datas:
                    del data['im']
                with open('dbg\\catches.txt', 'a+') as f:
                    f.write(json.dumps((str(start_time)[6:12] + '_' +str(event), datas)) + '\n')

        self.mouse.play_thread.join()
            
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
            for i in range(36): #range(self.var['FISHES_PER_ITER']):
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
        #blk 19 83 126
        #wht 102 136 173

        bg_col1 = im.getpixel(al(pos, (SLOT_SIZE-SLOT_GAP//2, SLOT_SIZE//2)))
        bg_col2 = im.getpixel(al(pos, (-SLOT_GAP//2, SLOT_SIZE//2)))

        selected_color = []
        for i in range(3):
            val = SELECTED_MIN[i] + ((bg_col1[i] + bg_col2[i])/512)*(SELECTED_MAX[i] - SELECTED_MIN[i])
            selected_color.append(val)

        isSelected = sdist(px1,selected_color) < 400 and sdist(px2,selected_color) < 400
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

def cTest():
    t.sleep(4)
    print('run')
    f = Fisher()
    f.fish()

if __name__ == "__main__":
    print('running fisher...')
    if 0:
        f = Fisher()
    else:
        t.sleep(3)
        f = Fisher()
        #f.run()
        f.test_fov()
    #cProfile.run('cTest()')

def showr(rx,ry,w=3):
    t.sleep(w)
    f.rotate_to(rx,ry)
    f.mouse.play_thread.join()
    f.handle_angle_correction()
    f.mouse.play_thread.join()
    print('DONE')
