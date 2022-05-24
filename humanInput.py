'''from settings import *

from basicHelpers import *'''

import ctypes
import random as r
import pyautogui as pag
import numpy as np
import time as t
import json

import threading, queue

if __name__ == '__main__':
    import keyboard

from multiprocessing import Process, Value, Array

pag.PAUSE = 0




def sdist(rgb1, rgb2 = (0,0,0)):
    return sum([(rgb1[i] - rgb2[i])**2 for i in range(len(rgb1))])

def dist(rgb1,rgb2 = (0,0,0)):
    return sdist(rgb1, rgb2) ** 0.5


ACTION_BLENDING = 0.4
def destination(action):
    x = 0
    y = 0
    t = 0
    for a in action:
        x += a[0]
        y += a[1]
        t += a[2]
    return x,y,t

class Action(object):
    def __init__(self, items):
        self.items = items
        dest = destination(items) 
        self.destination = dest
            
def get_actions(path='whip_movements.txt'):
    actions = []
    with open(path,'r') as file:
        data = file.read()
        lines = data.split('\n')
        for line in lines:
            if line:
                #print(line)
                action = json.loads(line)
                a = Action(action)
                if a.destination[0] and a.destination[1]:
                    actions.append(a)
    return actions

WHIP_ACTIONS = get_actions('whip_movements.txt')
NORMAL_ACTIONS = get_actions('normal_movements.txt')


def test2(speed):
    t.sleep(4)
    MOUSEEVENTF_MOVE = 0x0001
    for i in range(40):
        
        print(
            ctypes.windll.user32.mouse_event( MOUSEEVENTF_MOVE, speed, 0, 0, 0)
        )
        t.sleep(1/144)
        for i in range(speed//4):
                
            print(
                ctypes.windll.user32.mouse_event( MOUSEEVENTF_MOVE, -4, 0, 0, 0)
            )
            t.sleep(1/144)
    
def rotate(item, vx, vy):
    
    x = item[0]
    y = item[1]
    assert type(x) == int and type(y) == int
    
    if x == 0 and y == 0:
        return
    MOUSEEVENTF_MOVE = 0x0001 
    x_calc = ctypes.c_long(x)
    y_calc = ctypes.c_long(y)
    #print('mmove',x_calc,y_calc)
    attemptsLeft = 5
    while not ctypes.windll.user32.mouse_event( MOUSEEVENTF_MOVE, x_calc, y_calc, 0, 0):
        if attemptsLeft < 0:
            raise Exception('FAILED TO MOVE MOUSE')
        attemptsLeft -= 1
    vx.value += x
    vy.value += y


def play_thread_func(q, vx, vy):
    using = None
    start_time = None
    strings = ''
    while True:
        try:
            using = q.get(block=False)
            start_time = t.time()
        except queue.Empty:
            if using and len(using):
                new_time = t.time()
                next_item = using[0]
                strings += '\n> ' + str(new_time) + '_' + str(start_time) + '==' + str(new_time- start_time) + str( next_item)
                
                while new_time - start_time >= next_item[2] and using and len(using):
                    del using[0]
                    start_time += next_item[2]
                    rotate(next_item, vx, vy)
                    if len(using) == 0:
                        return
                    next_item = using[0]

            else:
                print('STRINGS\n' + strings)
                return
        #t.sleep(0.005)

'''
    action_time = 0
    items = action
    while len(items):
        start_time = t.time()
        item = items.pop(0)

        action_time = item[2]
        new_time = t.time()
        
        while action_time > new_time-start_time:
            #print(action_time, new_time-start_time)
            new_time = t.time()
        rotate(item, vx, vy)'''


class Mouse(object):
    def __init__(self):
        self.vx = Value('i', 0)
        self.vy = Value('i', 0)
        self.play_thread = None

        self.performing = []

        self.action_queue = queue.Queue()



    def choose_action(self, x,y, method, variety=3):
        bests = []
        dists = []
        for i,action in enumerate(method):
            action_best = 999999999
            for sx in range(-1,2,2):
                for sy in range(-1,2,2):
                    dest_xy = destination(action.items)[0] * sx, destination(action.items)[1] * sy
                    new_dist = sdist(dest_xy, (x,y))
                    if new_dist < action_best:
                        action_best = new_dist
                    
            for i in range(min(variety, len(bests))):
                if action_best < dists[i]:
                    dists.insert(i,action_best)
                    bests.insert(i,action)
                    dists = dists[:variety]
                    bests = bests[:variety]
                    break
            else:
                if len(bests) < variety:
                    dists.append(new_dist)
                    bests.append(action)
                    
        chosen = r.randint(0,len(bests)-1)
        return bests[chosen]

    
    def rotate_to(self, x,y, speed, method=WHIP_ACTIONS):
        if self.vx.value == x and self.vy.value == y and (self.play_thread and not self.play_thread.is_alive()):
            return
        it = 0
        start_pos = [self.vx.value, self.vy.value]
        #print('start = ', start_pos)
        #TODO
        ''' 
        for i,item in enumerate(self.performing):
            it += item[2]
            if it >= ACTION_BLENDING:
                self.performing = self.performing[:i]
                break
            blend = (ACTION_BLENDING - it) / ACTION_BLENDING
            item[0] = round(item[0] * blend)
            item[1] = round(item[1] * blend)
            start_pos[0] += item[0]
            start_pos[1] += item[1]
            '''

        rx = x - start_pos[0]
        ry = y - start_pos[1]
        t1 = t.time()
        act = self.choose_action(rx, ry, method)
        t2 = t.time()
        
        xscale = (rx)/act.destination[0]
        yscale = (ry)/act.destination[1]
        
        tscale = speed/act.destination[2]
        
        
        act_pos = [0,0,0]
        old_scaled_pos = (0,0,0)
        #if len(self.performing) < len(act.items):
        #    self.performing += [0] * (len(act.items) - len(self.performing))
        scaled_items = []
        for item in act.items:
            act_pos[0] += item[0]
            act_pos[1] += item[1]
            act_pos[2] = item[2]
                
            new_scaled_pos = (round(act_pos[0] * xscale), round(act_pos[1] * yscale))
            dx = new_scaled_pos[0] - old_scaled_pos[0] 
            dy = new_scaled_pos[1] - old_scaled_pos[1]
            dt = item[2] * tscale
            #print('act pos', act_pos, 'dd',dx,dy)
            old_scaled_pos = new_scaled_pos
            scaled_items.append([dx,dy,dt])

        t3 = t.time()
        def get_key(item):
            return item[2]
        
        #print(self.performing,'\n\n\n', scaled_items)


        print('INFO',act.destination, speed, destination(scaled_items))
        
        self.play(scaled_items) #sorted(self.performing + , key=get_key)
        print('CHOSE',t2-t1,t3-t2, t3-t.time() )
        #self.performing = 
            
            


    def play(self, action):
        print('playing', len(action), destination(action))
        t1 = t.time()
        self.action_queue.put(action)
        if not self.play_thread or not self.play_thread.is_alive():
            self.play_thread = threading.Thread(target=play_thread_func, daemon=True, args=(self.action_queue, self.vx, self.vy))
            self.play_thread.start()
        print('PLAY TIME', t.time()-t1)
    
            
    
def record_action_list(path='temp.txt'):
    pos = pag.position()
    while True:
        t.sleep(0.1)
        moves = []
        last_time = None
        start_pos = pag.position()
        print('Press R to start waiting for an action')
        while not keyboard.is_pressed('r'):
            pass
        print('waiting for an action from', start_pos)
        while last_time == None or t.time() - last_time < 0.1:
            
            new_pos = pag.position()
            
            if new_pos[0] == start_pos[0] and new_pos[1] == start_pos[1]:

                continue
            #print('last', last_time, new_pos, start_pos)
            new_time = t.time()
            if last_time == None:
                passed = 0
            else:
                passed = new_time - last_time
            
            moves.append( (new_pos[0] - start_pos[0], new_pos[1] - start_pos[1], passed) )
            start_pos = new_pos
            last_time = new_time

        dest = destination(moves)
        print('DONE', dest)
        print('test play action: press T, save action: press y/n')
        
        yy = False
        nn = False
        while not (yy or nn):
            yy = keyboard.is_pressed('y')
            nn = keyboard.is_pressed('n')
            tt = keyboard.is_pressed('t')
            if tt:
                print(moves)
                dupe = Action(moves[:])
                m = Mouse()
                print()
                m.play(dupe.items)
                print('playing...')
                m.play_thread.join()
                print('done')
            elif nn:
                moves = []

        if yy:
            
            print('wait done')
            data = json.dumps( moves )
            print(data)
            with open(path, 'a+') as file:
                file.write(data + '\n')
        
rr = record_action_list

if __name__ == '__main__':
    mm = Mouse()
    t.sleep(1)
    t1 = t.time()
    mm.rotate_to(100,10,0.1)
    mm.play_thread.join()
    print('time',t.time()-t1)
    #t.sleep(0.3)
    print('VXVY',mm.vx, mm.vy)
    #t.sleep(0.7)
    #print('VXVY',mm.vx, mm.vy)
    #t.sleep(1)

    '''mm.rotate_to(-100,-10,1)
    t.sleep(0.3)
    print('VXVY',mm.vx, mm.vy)
    t.sleep(0.7)
    print('VXVY',mm.vx, mm.vy)
    t.sleep(2)'''

'''
ACTION_BLENDING = 0.3
def destination(action):
    x = 0
    y = 0
    for a in action:
        x += a[0]
        y += a[1]
    return x,y

class Action(object):
    def __init__(self, items):
        self.items = items
        self.destination = destination(items)

def get_actions(path='whip_accurate_movements.txt'):
    actions = []
    with open(path,'r') as file:
        data = file.read()
        lines = data.split('\n')
        for line in lines:
            if line:
                print(line)
                action = json.loads(line)
                actions.append(Action(action))
    return actions


class Mouse(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.actions = []
        self.accurate_whips = get_actions('whip_accurate_movements.txt')
        self.whips = get_actions('whip_accurate_movements.txt')
        self.drags = get_actions('whip_accurate_movements.txt')
        self.normals = get_actions('whip_accurate_movements.txt')
        self.performing = []

    def options(self, move, method=self.normals):
        for action in method:
            
        
    move_methods = ['drag', 'whip', 'whip_accurate', 'normal']
    def rotate_to(self, pos, method='normal'):
        it = 0
        for i,item in enumerate(self.performing):
            it += item[2]
            if it >= ACTION_BLENDER:
                self.performing = self.performing[:i]
                break
            blend = (ACTION_BLENDING - it) / ACTION_BLENDING
            item[0] *= blend
            item[1] *= blend

        offset = destination(self.performing)
        
        pos = pos[0] - offset[0], pos[1] - offset[1]
        
            
        
    
    def rotate(self, item):
        x = item[0]
        y = item[1]
        assert type(x) == int and type(y) == int
        
        if x == 0 and y == 0:
            return
        MOUSEEVENTF_MOVE = 0x0001 
        x_calc = ctypes.c_long(x)
        y_calc = ctypes.c_long(y)
        #print('mmove',x_calc,y_calc)
        attemptsLeft = 5
        while not ctypes.windll.user32.mouse_event( MOUSEEVENTF_MOVE, x_calc, y_calc, 0, 0):
            if attemptsLeft < 0:
                raise Exception('FAILED TO MOVE MOUSE')
            attemptsLeft -= 1
        self.x += x
        self.y += y
    
    def set_desired(pos, method='whip_accurate'):
        pass

def g():
    pos = pag.position()
    while True:
        input('ready')
        moves = []
        last_time = None
        start_pos = pag.position()
        while last_time == None or t.time() - last_time < 0.1:
            
            new_pos = pag.position()
            print('last', last_time, new_pos, start_pos)
            if new_pos[0] == start_pos[0] and new_pos[1] == start_pos[1]:

                continue
            new_time = t.time()
            if last_time == None:
                passed = 0
            else:
                passed = new_time - last_time
            
            moves.append( (new_pos[0] - start_pos[0], new_pos[1] - start_pos[1], passed) )
            start_pos = new_pos
            last_time = new_time
        
        tt = input('cancl')
        if len(tt):
            continue
        data = json.dumps( moves )
        print(data)
        with open('whip_accurate_movements.txt', 'a+') as file:
            file.write(data + '\n')


#g()        



def m(x=100,y=100):
    actions = get_actions()
    best = None
    best_dist = 99999
    for i,action in enumerate(actions):
        new_dist = dist(destination(action), (x,y))
        if new_dist < best_dist:
            best_dist = new_dist
            best = action
    print('best',i)

def play(action):
    start_time = t.time()
    passed_time = 0
    action_time = 0
    mouse = Mouse()
    for item in action:
        action_time += item[2]
        passed_time = t.time() - start_time

        while passed_time < action_time:
            passed_time = t.time() - start_time
            
        mouse.rotate(item)
        
        
        

m()
'''
'''   start
    moves = []
    while True:
        new_pos = pag.position()
        if new_pos != pos:
            last_move_time = t.time()
'''
