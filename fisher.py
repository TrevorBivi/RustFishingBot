import time as t
#from scipy.stats import linregress

from settings import *
from basicHelpers import *
from fishingHelpers import *

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

    def rotate(self, rx, ry):
        dbg('@rotate')
        desired = rx
        original = self.rx
        new_x = self.rx + rx
        if new_x > MAX_ROT:
            rx = MAX_ROT - self.rx
        elif new_x < MIN_ROT:
            rx = MIN_ROT + self.rx
        actual = rx
        slept = False
        while rx > self.var['MSPEED']:
            rx -= self.var['MSPEED']
            cx = int(self.var['MSPEED']  * SENSITIVITY)
            self.dx += cx
            wm_mouse_move(cx,0)
            slept = True
            #print('loop pos', rx)
            t.sleep(1/90)
            
        while rx < -self.var['MSPEED']:
            rx += self.var['MSPEED']
            cx = int(-self.var['MSPEED']  * SENSITIVITY)
            self.dx += cx
            wm_mouse_move(cx,0)
            slept = True
            #print('loop neg', rx)
            t.sleep(1/90)

        cx = int(rx * SENSITIVITY)
        self.dx += cx
        self.rx = self.dx / SENSITIVITY
        #print('final', rx)
        wm_mouse_move(cx,0)
        #print('original', original, 'des dx', desired, ' (to ', new_x, ') actual', actual, ' new',self.rx) 
        dbg('% rotate  - slept' + str(slept))
        
    def rotate_to(self, rx, ry):
        dbg('@rotate_to')
        dt = t.time()
        dx = rx - self.rx
        dy = ry - self.ry
        self.rotate(dx,dy)
        dbg('% rotate_to')
        
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
        print('~~desired_keys')
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
            
        self.reset_rotation()
        self.heat = 0
        self.cooling = False
       
        if active_rod(im) == None:
            pressSlot(inactive_rod(im))

        if not 'right' in self.buttons:
            self.add_button('right')
            t.sleep(g(1.3))
         
        self.add_button('left')
        t.sleep(g(0.2))
        self.rm_button('left')
        t.sleep(1)
        self.rotate_to(35,0)
        t.sleep(g(2))
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
                    
                    if px[0] > px[1] > px[2]:
                        self.switch_keys(['s','d'])
                        for time_length in (self.var['FIRST_PULL_TIME'], self.var['FIRST_COOL_TIME']):
                            test_time = t.time()
                            event = None
                            while t.time() - test_time < time_length and not event:
                                im = iGrab.grab()
                                self.fish_left(im)
                                event = handle_event(im)
                                if event:
                                    dbg('%handle_pull - event3')
                                    return event
                                t.sleep(self.var['SCANTIME'])
                                
                            self.switch_keys([])
                        dbg('%handle_pull - pulled')
                        return None
        dbg('%handle_pull - maxwait')
        return None
    
    def fish_left(self,im=None):
        dbg('@fish_left')
        if im == None:
            im = iGrab.grab()
            
        def handle_rotation():
            self.rotate_to(-10,0)
        
        def is_line(x,y):
            px = im.getpixel((x,y))
            if px[0] < 95 and px[1] < 95 and px[2] < 95:
                return True

        wall_r = (self.rx - self.var['MIN_ROT']) / (self.var['MAX_ROT'] - self.var['MIN_ROT'])
        wall_pos = (
            FISH_LEFT_WALL_MIN[0] + wall_r * (FISH_LEFT_WALL_MAX[0]-FISH_LEFT_WALL_MIN[0]),
            FISH_LEFT_WALL_MIN[1] + wall_r * (FISH_LEFT_WALL_MAX[1]-FISH_LEFT_WALL_MIN[1]))
        #wall_pos = FISH_LEFT_WALL_MIN
        scan_line = Line(wall_pos, FISH_LEFT_PLAYER)
        hot_pos = slot_pos(0,0)
        #print(scan_line.p1, scan_line.p2)
        for y in range(int(scan_line.p1[1]), int(scan_line.p2[1])):
            x = int(scan_line.f(y))
            if hot_pos[1] < y < hot_pos[1] + SLOT_SIZE:
                continue
            
            if is_line(x, y):
                im.putpixel((x,y), (255,0,0))
                self.switch_keys(['d'])
                handle_rotation()
                dbg('%fish_left - true')
                return True
            im.putpixel((x,y), (0,0,255))
        dbg('%fish_left - false')
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
            for x in range(RAISED_ROD_TL[0], RAISED_ROD_BR[0], RAISED_ROD_SPEED):
                for y in range(RAISED_ROD_TL[1], RAISED_ROD_BR[1], RAISED_ROD_SPEED):
                    #print('raised rod check',x,y, px)
                    px = im.getpixel((x,y))
                    #print('raised rod check',x,y, px)
                    im.putpixel((x,y), (0,255,0))
                    if dist(px, (0,0,0)) < 80:
                        im.putpixel((x,y), (0,0,255))
                        return 'SNAP'
            return None

        if not im:
            im = iGrab.grab()

        if got_pickup(im): # success
            other_rod = inactive_rod(im)
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
        ret = rod_snapped()
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
        while not event or new_time - start_time > self.var['MAXWAIT']:
            last_time = new_time
            new_time = t.time()
            time_change = new_time - last_time
            dbg('* fight loop -  last time change' +  str(time_change), 1)
            
            im = iGrab.grab()
            if not self.fish_left(im):
                self.rotate(1,0)
            self.update_actions(time_change)
            event = self.event_check(im)
            last_ims.append(im)
            last_ims = last_ims[-110:]
            #t.sleep(max(0,self.var['SCANTIME'] - time_change))
            #print('sleeping', max(0,self.var['SCANTIME'] - time_change))
        if event == 'SNAP':
            dbg('# save snap pics')
            for i, snap_im in enumerate(last_ims[:25]):
                snap_im.save('dbg\\' + str(new_time) + '_' + str(i) + '.png')

        dbg('%handle_fight')
        return event

    def fish(self):
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
            loop_sum = manage_inventory()
            pag.press('space')
            t.sleep(g(0.6))
            
            new_score = 0
            for i, ft in enumerate(fish_names):
                total_fish[ft] += loop_sum[i]
                new_score += loop_sum[i] * fish_values[i]
            total_score += new_score

            log_time = t.time()
            passed = log_time - start_time
            log_data = {'type': 'ITER','id':run_id, 'average':total_score / passed, 'new average':new_score/passed, 'score': total_score, 'new score': new_score, 'snaps':snaps, 'timeouts':timeouts, 'catches':catches, 'unknowns':unknowns, 'fish':total_fish} 
            log(str(log_data))
            print('done loop')
            new_time = t.time()
            
        self.reset_rotation()
        return total_fish
