from settings import *
from basicHelpers import *
from PIL import ImageGrab as iGrab
import time as t
import pyautogui as pag
import cv2
import numpy as np


wormt = get_template('worm.png')
grubt = get_template('grub.png')
#rodt = get_template('rod.png')
skullt = get_template('skull.png')
buckett = get_template('bucket.png')
bottlet = get_template('bottle.png')

anchovyt = get_template('anchovy.png')
sardinet = get_template('sardine.png')
herringt = get_template('herring.png')
yellowt = get_template('yellow.png')
salmont = get_template('salmon.png')
catfisht = get_template('catfish.png')
troutt = get_template('trout.png')
sharkt = get_template('shark.png')

fisht = get_template('fish.png')
dropt = get_template('drop.png')
gutt = get_template('gut.png')
cardt = get_template('card.png')
clotht = get_template('cloth.png')
flaret = get_template('flare.png')
scrapt = get_template('scrap.png')
fatt = get_template('fat.png')
pistolbullett = get_template('pistolbullet.png')
bonet = get_template('bone.png')


def slot_pos(x,y):
    if y == 0:
        ry = HOT_POS[1]
        rx = HOT_POS[0] + SLOT_SIZE * x
    else:
        ry = BP_POS[1] + SLOT_SIZE * (4-y)
        rx = BP_POS[0] + SLOT_SIZE * x
    return rx, ry

def slotState(i, im=None):
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

    isSelected = dist(px1,(55,100,146)) < 30 and dist(px2,(55,100,146)) < 30
    print(hasHealth, isFull, isSelected)
    return hasHealth, isFull, isSelected

def inactive_rod(im):
    if not im:
        im = iGrab.grab()
    for i in range(6):
        ss = slotState(i)
        if ss[0] and ss[1] and not ss[2]:
            return i

def active_rod(im):
    if not im:
        im = iGrab.grab()
    for i in range(6):
        ss = slotState(i)
        if ss[0] and ss[1] and ss[2]:
            return i

def pressSlot(i):
    assert 0 <= i <= 5
    print('+ slot ' + str(i+1))
    pag.press(str(i+1))


fish_templates = [sardinet, anchovyt, herringt, troutt, yellowt, salmont, catfisht, sharkt]
fish_values = [0, 0, 0, 30/5, 50/5, 55/2, 65/2, 90/2]
fish_names = ['sardine', 'anchovy', 'herring', 'trout', 'yellow', 'salmon', 'catfish', 'shark']

def manage_inventory():
    tl = slot_pos(0, 4)
    br = al(slot_pos(6, 0), (SLOT_SIZE, SLOT_SIZE))
    inv_box = tl[0], tl[1], br[0], br[1]
    print('ive box', inv_box)
    action_box = tl[0], 0, br[0], tl[1]

    gut = fish_templates
    junk = [fisht, flaret, cardt, fatt, scrapt, clotht, bonet, pistolbullett, skullt] # # bottlet,  skullt,  buckett
    im = None
         
    print('=tab OPEN TIDY')
    pag.keyDown('tab')
    t.sleep(g(0.2))
    pag.keyUp('tab')
   
    ### GUT
    i = 0
    amntfish = [0] * len(gut)
    im = iGrab.grab()
    for i, gt in enumerate(gut):
        pos = match_template(gt, im, 0.98, inv_box)
        print('? search for', fish_names[i],pos)
        while pos:
            print('^ found')
            pos = pos[0]
            pag.click(pos[0], pos[1])
            t.sleep(g(0.2))
            im = iGrab.grab()
            gutpos = match_template(gutt, im, 0.975, action_box)
            print('-gutt search',gutpos)
            while gutpos:
                print('^gut text found')
                amntfish[i] += 1
                gutpos = gutpos[0]
                pag.click(gutpos[0], gutpos[1])
                t.sleep(0.15)
                im = iGrab.grab()
                gutpos = match_template(gutt,im, 0.975, action_box)
                print('-- gutt search',gutpos)
            print('?? search for', fish_names[i],pos)
            pos = match_template(gt,im, 0.98, inv_box)
            print('size',im.size)
        i += 1

    ### REFILL
    def meatmatch(m1,m2):
        if m1 == None and m2 == None:
            print('meat match')
            return True
        elif m1 != None and m2 != None:
            return dist(m1[0],m2[0]) < 3
    
    for i in range(6):
        pole = slotState(i,im)
        if pole[0]:
            oldmeatpos = None
            meatpos = match_template(fisht, im, 0.98, inv_box)
            while meatpos and not meatmatch(oldmeatpos, meatpos):
                print('meating',meatpos, i)
                pag.moveTo(meatpos[0])
                t.sleep(0.15)
                pag.mouseDown()
                t.sleep(0.15)
                pole_pos = al(slot_pos(i,0), (SLOT_SIZE // 2, SLOT_SIZE // 2))
                pag.moveTo(pole_pos)
                t.sleep(0.2)
                pag.mouseUp()
                t.sleep(0.1)
                oldmeatpos = meatpos
                im = iGrab.grab()
                meatpos = match_template(fisht,im, 0.98, inv_box)

    ### JUNK
    used = junk
    for j in junk:
        pos = match_template(j, im, 0.98, inv_box)
        print('?j',pos)
        while pos:
            print('JUNK [PS',pos)
            pos = pos[0]
            pag.moveTo(pos)
            t.sleep(0.1)
            pag.click()
            t.sleep(0.2)
            im = iGrab.grab()
            droppos = match_template(dropt, im, 0.98, action_box)
            if droppos:
                droppos = droppos[0]
                pag.click(droppos[0], droppos[1])
                t.sleep(0.15)
            im = iGrab.grab()
            pos = match_template(j,im, 0.98, inv_box)                

    t.sleep(0.2)
    
    print('=tab CLOSETIDY')
    pag.keyDown('tab')
    t.sleep(g(0.13,0.15))
    pag.keyUp('tab')
    t.sleep(0.5)
    return amntfish

def status_pixel(i, im=None):
    if im == None:
        im = iGrab.grab()

    x = STATUS_0_POS[0]
    y = STATUS_0_POS[1] - STATUS_HEIGHT * i
    return im.getpixel((x,y))

def got_pickup(im=None):
    t1=t.time()
    if im == None:
        im = iGrab.grab()
    for i in range(2,6):
        if dist(status_pixel(i,im), (88,102,67)) < 15:
            return True
    return False


def get_player_stats(im=None, iters=4):
    WATER_LOW = al((72, 139, 192), (-5,-5,-5))
    WATER_HIGH = al((81, 157, 215), (5,5,5))

    HEALTH_LOW = al((125,164,64), (-5,-5,-5))
    HEALTH_HIGH = al((144,189,76), (5,5,5))

    HUNGER_LOW = al((183, 109, 67), (-5,-5,-5))
    HUNGER_HIGH = al((201, 118, 67), (5,5,5))

    colors = ( (WATER_LOW, WATER_HIGH), (HEALTH_LOW, HEALTH_HIGH), (HUNGER_LOW, HUNGER_HIGH) )

    stats = []
    
    if im == None:
        im = iGrab.grab()
    for s in range(3):
        percent = 0.5
        for i in range(2,iters+2):
            px = im.getpixel((int(PLAYER_BAR_LEFT + percent * PLAYER_BAR_WIDTH), PLAYER_HP_HEIGHT))
            for c in range(3):
                if not (colors[i][0][c] <= px[c] <= colors[i][1][c]):
                    percent -= 0.5 ** i
                    break
            else:
                percent += 0.5 ** i
        stats.append(percent)
    return stats

def manage_inventory_2():
    tl = slot_pos(0, 4)
    br = al(slot_pos(6, 0), (SLOT_SIZE, SLOT_SIZE))
    inv_box = tl[0], tl[1], br[0], br[1]
    print('ive box', inv_box)
    action_box = tl[0], 0, br[0], tl[1]

    gut = fish_templates
    junk = [fisht, flaret, cardt, fatt, scrapt, clotht, bonet, pistolbullett, skullt] # # bottlet,  skullt,  buckett
    im = None
         
    print('=tab OPEN TIDY')
    pag.keyDown('tab')
    t.sleep(g(0.13,0.15))
    pag.keyUp('tab')

    def gut_type(fsh):
        im = iGrab.grab()

        #select fish
        fish_pos = match_template(fsh, im, 0.98, inv_box)
        while fish_pos:
            pag.moveTo(fish_pos[0])
            t.sleep(0.15)
            pag.click()
            t.sleep(0.2)

            #gut fish
            im = iGrab.grab()
            gut_pos = match_template(gutt, im, 0.98, action_box)
            if gut_pos:
                pag.moveTo(gut_pos)
                t.sleep(0.15)
                pag.click()
                t.sleep(0.15)
                
                im = iGrab.grab()
                fish_pos = match_template(fish, im, 0.98, inv_box)

    def fill_rods():
        im = iGrab.grab()
        
        #For each rod slot
        for i in range(6):
            pole = slotState(i,im)
            if pole[0]:
                
                #Continue filling until there is no meat left or the stack isn't used (rod full)
                old_meat_pos = (0,0)
                meat_pos = match_template(fisht, im, 0.98, inv_box)
                while meat_pos and dist(old_meat_pos, meat_pos[0]) > SLOT_SIZE / 2:
                    pag.moveTo(meat_pos[0])
                    pag.mouseDown()
                    t.sleep(g(0.15))
                    pag.moveTo(al(slot_pos(i,0), (SLOT_SIZE//2, SLOT_SIZE//2)))#rod pos
                    t.sleep(g(0.15))
                    pag.mouseUp()
                    t.sleep(g(0.15))
                    
                #Ran out of meat
                if not meat_pos:
                    return False
        return True

def deposit_items():
    MIN_Y = 4
    im = iGrab.grab()
    inv_box = None
    for fsh in fish_templates[3:]:
        fsh_pos = match_template(fsh_templates, im, 0.98, inv_box)
        while fsh_pos:
            pag.moveTo(fsh_pos[0])
            t.sleep(g(0.15))
            pag.mouseDown(button='right')
            t.sleep(g(0.05))
            pag.mouseUp(button='right')
            t.sleep(g(0.15))
            im = iGrab.grab()
            fsh_pos = match_template(fsh_templates, im, 0.98, inv_box)
