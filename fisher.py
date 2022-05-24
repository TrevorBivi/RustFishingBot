import time as t
#from scipy.stats import linregress
from PIL import ImageDraw, Image
from sympy import Q
from settings import *
from basicHelpers import *
from fishingHelpers import *
from humanInput import *

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
                dbg('>'+nk)
                pag.keyDown(nk)
        for ok in self.keys:
            if not ok in keys:
                dbg('<'+ok)
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
            if abs(pos[0] - SCREEN_SIZEsdsd[0] / 2) < i_x(self.var['DIAGONALWIDTH']):
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
        self.heat = 0
        self.cooling = False
        self.brightness = get_brightness(im)
       
        if self.active_rod(im) == None:
            pressSlot(self.inactive_rod(im))

        if not 'right' in self.buttons:
            self.add_button('right')
            t.sleep(g(1.3))
         
        self.add_button('left')
        t.sleep(g(0.2))
        self.rm_button('left')
        t.sleep(1)
        
        self.rotate_to(g(20),20,)
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
        
    def handle_pull(self):
        dbg('@handle_pull')
        def handle_event(im):
            event = self.event_check(im)
            if event:
                self.switch_keys([])
                self.event_wait(event)
                dbg('%handle_pull - event')
                return event
        
        def is_rod(px):
            chan_max = lerp(self.brightness, LINE_BRIGHTNESS_CURVE)
            if px[0] <= chan_max and px[1] <= chan_max and px[2] <= chan_max:
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
                        for time_length in (self.var['FIRST_PULL_TIME'], self.var['FIRST_COOL_TIME']):
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
                                
                            self.switch_keys([])
                        dbg('%handle_pull - pulled')
                        return None
        dbg('%handle_pull - maxwait')
        return None
    
    def handle_angle_correction(self,im=None, vx = None, vy = None):
        dbg('@handle_angle_correction')
        debug = False
        if self.fishing_left_time and t.time() - self.fishing_left_time < 2:
            dbg('%handle_angle_correction - time skip')
            return True
        if vx == None:
            vx = self.mouse.vx.value
        if vy == None:
            vy = self.mouse.vy.value

        if im == None:
            im = iGrab.grab()
        old_fishing_left = self.fishing_left
        def handle_rotation():
            if self.fishing_left and not old_fishing_left:
                print('ROTTEATE LEFT!!!!')
                #self.switch_keys(['d'])
                self.rotate_to(-10,0,0.2)
            elif not self.fishing_left and old_fishing_left:
                print('ROTTEATE RIGH    T!!!!')
                self.rotate_to(50, 0, 3 )
            #else:
                #print('no action', self.brightness)
        def is_line(x,y):
            px = im.getpixel((x,y))
            chan_max = 95 * self.brightness + 0
            if px[0] <= chan_max and px[1] <= chan_max and px[2]  <= chan_max:
                return True


        hot_pos = slot_pos(0,0)
        
        

        scan_len = min(6, abs( 0.8 /  m.sin( m.radians(20.9) - m.radians(self.mouse.vx.value / SENSITIVITY) )))
        

        FISH_LEFT_P2 = [ -0.3 , 0, 0.5 ]
        #FISH_LEFT_P1 = [ -2.25, 0,  ]
        rot = (m.radians(vy / SENSITIVITY) * 1,m.radians(vx / SENSITIVITY),0)#,0)
        #print('left rot',)
        #rot = (0.0, -0.17453292519943295, 0)
        snap_rot = rot[0], rot[1] - m.radians(50), rot[0]


        z_dist = 2.4 / max(0.001, abs( m.tan(snap_rot[1])) )
        #print('zdist', z_dist)
        FISH_LEFT_P1 = [ -2.4, -0.8, min(z_dist, 6.7) ]

        FISH_LEFT_P2 = [ m.sin(snap_rot[1] - m.radians(20.5)) ,-0.8   ,m.cos(snap_rot[1] - m.radians(20.5)) ]

        #FISH_LEFT_P1 = [-2.3, 0, 6]
        #FISH_LEFT_P2     = [0.5, 0, 6]
          #2.3 2.4
        
        #pp1 = weak_proj(FISH_LEFT_P1, (m.degrees(rot[0]), m.degrees(rot[1])))  # persp_proj(FISH_LEFT_P1, rot )  
        pp1 = persp_proj(FISH_LEFT_P1, rot)  # persp_proj(FISH_LEFT_P1, rot )  
        #pp2 = weak_proj(FISH_LEFT_P2, (m.degrees(rot[0]), m.degrees(rot[1])))  # persp_proj(FISH_LEFT_P1, rot )  
        pp2 = persp_proj(FISH_LEFT_P2, rot)  # persp_proj(FISH_LEFT_P1, rot )  

        if pp1[1] > pp2[1]:
            scan_line = Line(pp2,pp1)
        else:
            #print('aa',pp1,pp2)
            scan_line = Line(pp1,pp2)
        scan_iter = scan_line.get_iter()
        #print('P1', pp1, 'P2', pp2)
        #print('rot' + str(rot) + 'MIN MAX' + str(scan_iter.min) + ', ' + str(scan_iter.max))

        #prin   t('FI33334555555555555555553333SH LEFT')
        #print(scan_line.p1, scan_line.p2)
        self.fishing_left = False

        for x,y in scan_iter:
            #print('ITER',x,y)
            if hot_pos[1] < y < hot_pos[1] + SLOT_SIZE and hot_pos[0] < x < hot_pos[0] + SLOT_SIZE * 6:
                continue

            if is_line(x, y):
                self.fishing_left_time = t.time()

                #if debug:
                    #im.putpixel((x+2,y+1), (255,0,255))
                    #im.putpixel((x+3,y+1), (255,0,255))
                    #im.putpixel((x+2,y+1), (255,0,255))
                    #im.putpixel((x+3,y+1), (255,0,255))
                
                #im.putpixel((x+1,y+1), (255,255,0))
                #im.putpixel((x+1,y), (255,255,0))
                #im.putpixel((x,y+1), (255,255,0))
                #im.putpixel((x,y), (255,255,0))
                #im.putpixel((x+2,y+1), (255,255,0))
                #im.putpixel((x+2,y), (255,255,0))
                #im.putpixel((x+3,y+1), (255,255,0))
                #im.putpixel((x+3,y), (255,255,0))
                self.fishing_left = True
                '''im.putpixel((x-1,y), (255,0,0))
                im.putpixel((x+1,y), (255,0,0))
                im.putpixel((x+4,y), (255,0,0))
                im.putpixel((x+5,y), (255,0,0))
                im.putpixel((x+6,y), (255,0,0))'''
                #break
            b=0
            px = im.getpixel((x,y))
            chan_max = 95 * self.brightness + 2
            if px[0] <= chan_max:
                b += 1
            if  px[1] <= chan_max:
                b += 2
            if  px[2] <= chan_max:
                b += 4
            if chan_max >= 2:
                b += 8
            if is_line(x,y):
                b += 16
            #print('check line', x,y)
            if debug:
                if self.fishing_left:
                    im.putpixel((x,y), (0,255,0))
                else:
                    im.putpixel((x,y), (0,0,255))
            
        
        handle_rotation()
        #draw = ImageDraw.Draw(im)
        #draw.line((pp2, pp1), fill=(250,0,0))
        #print('ppppppppppppp', pp1,pp2)

        #im = im.crop((0,720,2560/2,1440))
        #im = im.convert('L')
        if debug: #self.fishing_left:
            #im = im.crop((0,1440//3,2560//2,1440))
            im = im.crop((0,0,2560,1440))
            im.thumbnail( (2560//6,1440//6  ) , Image.NEAREST)
            if self.fishing_left:
                im.save('dbg/fff' + str(t.time()) + '.png')
            else:
                im.save('dbg/ggggg' + str(t.time()) + '.png')

        #im.save('dbg/asdas' + str(t.time()) + '.png')
        #sprint('FISHLEFT',self.fishing_left, 95 * self.brightness + 2, )
        dbg('%handle_angle_correction - ' +str(self.fishing_left))
        return self.fishing_left
        #im.show()

    def update_actions(self, last_action_time):
        dbg('@update_actions')
        if self.cooling:
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
                self.switch_keys(desired)
        dbg('%update_actions')

    def event_check(self, im=None):
        dbg('@event_check')
        def rod_snapped():
            chan_max = lerp(self.brightness, LINE_BRIGHTNESS_CURVE)+1
            #print('rod max', chan_max)
            for x in range(RAISED_ROD_TL[0], RAISED_ROD_BR[0], RAISED_ROD_SPEED):
                for y in range(RAISED_ROD_TL[1], RAISED_ROD_BR[1], RAISED_ROD_SPEED):
                    #print('raised rod check',x,y, px)
                    px = im.getpixel((x,y))
                    #print('raised rod check',x,y, px)
                    im.putpixel((x,y), (0,255,0))

                    if px[0] <= chan_max and px[1] <= chan_max and px[2] <= chan_max:
                        im.putpixel((x,y), (0,0,255))
                        return 'SNAP'
            return None
        
        BOBBER_PASS_G_CHAN = lerp(self.brightness, [(0,18-4), (1, 36-5)] )
        BOBBER_PASS_B_CHAN = lerp(self.brightness,[(0,31-4), (1,57-5)])
        BOBBER_FAIL_R_CHAN = lerp(self.brightness,[(0,33-4), (1,56-5)])

        def rod_snapped_night():
            for x in range (BOBBER_HOLO_TL[0], BOBBER_HOLO_BR[0], BOBBER_HOLO_SPEED):
                for y in range (BOBBER_HOLO_TL[1], BOBBER_HOLO_BR[1], BOBBER_HOLO_SPEED):
                    px = im.getpixel((x,y))
                    if px[0] > BOBBER_FAIL_R_CHAN and px[0] > px[2] * 4:
                        return 'SNAP'
                    elif px[2] > BOBBER_PASS_B_CHAN and px[1] > BOBBER_PASS_G_CHAN and px[1] > px[0] * 4:
                        return 'SNAP'

        if not im:
            im = iGrab.grab()

        if got_pickup(im): # success
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
        if self.brightness > 0.045:
            #print('NIGHT SNAP\n;lllllllllllllll\nlllllllllllll')
            ret =  rod_snapped()
        else:
            ret = rod_snapped_night()
        dbg('%event_check - rodsnapped=' + str(ret))
        return ret

    def handle_fight(self):
        dbg('@handle_fight')
        im = iGrab.grab()
        event = self.event_check()
        start_time = t.time()
        last_time = start_time
        new_time = start_time
        last_ims = []
        iters = 0

        while not event or new_time - start_time > self.var['MAXWAIT']:
            last_time = new_time
            new_time = t.time()
            time_change = new_time - last_time
            dbg('* fight loop -  last time change' +  str(time_change) + ' bright' + str(self.brightness), 0 )
            
            vx = self.mouse.vx.value
            vy = self.mouse.vy.value
            im = iGrab.grab()
            self.handle_angle_correction(im, vx, vy)

            self.update_actions(time_change)
            if iters % 3 == 0:
                event = self.event_check(im)
                self.brightness = get_brightness(im)
            
            #last_ims.append(im)
            #last_ims = last_ims[-110:]
            iters += 1
            if iters % 4 == 0:
                print('iter time', time_change)
            #t.sleep(max(0,self.var['SCANTIME'] - time_change))
            #print('sleeping', max(0,self.var['SCANTIME'] - time_change))
        if event == 'SNAP':
            dbg('# save snap pics')
            for i, snap_im in enumerate(last_ims[-1:]):
                snap_im.save('dbg\\' + str(new_time) + '_' + str(i) + '.png')

        dbg('%handle_fight')
        return event

    def fish(self):
        #   print('FI33333333SH LEFT')
        #self.handle_angle_correction()
        print('### cast')
        self.handle_cast()
        print('### pull wait')
        res = self.handle_pull()
        if res:
            print('!!! PULL EVENT')
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
            for i in range(self.var['FISHES_PER_ITER']):
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
                if dist(px,(115,140,68)) < 15:
                    
                    hasHealth = True
                    break
        px = im.getpixel(full)
        isFull = dist(px,(227,227,227)) < 30
        
        px1 = im.getpixel(selected1)
        px2 = im.getpixel(selected2)
        selected_color = (
            SELECTED_MIN[0] + self.brightness * (SELECTED_MAX[0] - SELECTED_MIN[0]),
            SELECTED_MIN[1] + self.brightness * (SELECTED_MAX[1] - SELECTED_MIN[1]),
            SELECTED_MIN[2] + self.brightness * (SELECTED_MAX[2] - SELECTED_MIN[2]),
        )
        isSelected = dist(px1,selected_color) < 30 and dist(px2,selected_color) < 30
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

    def inv_management(self):
        loop_sum = manage_inventory()
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
                t.sleep(0.2)
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
