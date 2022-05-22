from settings import *
from basicHelpers import *
from PIL import ImageGrab as iGrab
import time as t
import pyautogui as pag



templates = {
'worm': get_template('worm.png'),
'grub': get_template('grub.png'),
'skull': get_template('skull.png'),
'bucket': get_template('bucket.png'),
'bottle': get_template('bottle.png'),

'anchovy': get_template('anchovy.png'),
'sardine': get_template('sardine.png'),
'herring': get_template('herring.png'),
'yellow': get_template('yellow.png'),
'salmon': get_template('salmon.png'),
'catfish': get_template('catfish.png'),
'trout': get_template('trout.png'),
'shark': get_template('shark.png'),

'fish': get_template('fish.png'),
'drop': get_template('drop.png'),
'gut': get_template('gut.png'),
'card': get_template('card.png'),
'cloth': get_template('cloth.png'),
'flare': get_template('flare.png'),
'scrap': get_template('scrap.png'),
'fat': get_template('fat.png'),
'pistolbullet': get_template('pistolbullet.png'),
'bone': get_template('bone.png'),
}'''


def slot_pos(x,y):
    if y == 0:
        ry = HOT_POS[1]
        rx = HOT_POS[0] + SLOT_SIZE * x
    else:
        ry = BP_POS[1] + SLOT_SIZE * (4-y)
        rx = BP_POS[0] + SLOT_SIZE * x
    return rx, ry

def slot_state(i, im=None, brightness = None):
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

    if brightness == None:
        return hasHealth, isFull
    
    px1 = im.getpixel(selected1)
    px2 = im.getpixel(selected2)
    selected_color = (
        SELECTED_MIN[0] + brightness * (SELECTED_MAX[0] - SELECTED_MIN[0]),
        SELECTED_MIN[1] + brightness * (SELECTED_MAX[1] - SELECTED_MIN[1]),
        SELECTED_MIN[2] + brightness * (SELECTED_MAX[2] - SELECTED_MIN[2]),
    )
    isSelected = dist(px1,selected_color) < 30 and dist(px2,selected_color) < 30
    print(hasHealth, isFull, isSelected)
    return hasHealth, isFull, isSelected

def pressSlot(i):
    assert 0 <= i <= 5
    print('+ slot ' + str(i+1))
    pag.press(str(i+1))


fish_values = [0, 0, 0, 30/5, 50/5, 55/2, 65/2, 90/2]
fish_names = ['sardine', 'anchovy', 'herring', 'trout', 'yellow', 'salmon', 'catfish', 'shark']

def manage_inventory():
    tl = slot_pos(0, 4)
    br = al(slot_pos(6, 0), (SLOT_SIZE, SLOT_SIZE))
    inv_box = tl[0], tl[1], br[0], br[1]
    print('ive box', inv_box)
    action_box = tl[0], 0, br[0], tl[1]

    gut = fish_names
    junk = ['fish', 'flare', 'card', 'fat', 'scrap', 'cloth', 'bone', 'pistolbullet', 'skull'] # # bottle', ' skullt,  buckett
    im = None
         
    print('=tab OPEN TIDY')
    pag.keyDown('tab')
    t.sleep(g(0.2))
    pag.keyUp('tab')
   
    ### GUT
    i = 0
    amntfish = [0] * len(gut)
    im = iGrab.grab()
    for i, gt_name in enumerate(gut):
        gt = templates[gt_name]
        pos = match_template(gt, im, 0.98, inv_box)
        print('? search for', fish_names[i],pos)
        while pos:
            print('^ found')
            pos = pos[0]
            pag.click(pos[0], pos[1])
            t.sleep(g(0.2))
            im = iGrab.grab()
            gutpos = match_template(templates['gut'], im, 0.975, action_box)
            print('-gutt search',gutpos)
            while gutpos:
                print('^gut text found')
                amntfish[i] += 1
                gutpos = gutpos[0]
                pag.click(gutpos[0], gutpos[1])
                t.sleep(0.15)
                im = iGrab.grab()
                gutpos = match_template(templates['gut'],im, 0.975, action_box)
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
        pole = slot_state(i,im)
        if pole[0]:
            oldmeatpos = None
            meatpos = match_template(templates['fish'], im, 0.98, inv_box)
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
                meatpos = match_template(templates['fish'], im, 0.98, inv_box)

    ### JUNK
    used = junk
    for j_name in junk:
        j = templates[j_name]
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
            droppos = match_template(templates['drop'], im, 0.98, action_box)
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

def deposit_items():
    MIN_Y = 4
    im = iGrab.grab()
    inv_box = None
    for fsh in fish_templates[3:]:
        fsh_pos = match_template(fsh, im, 0.98, inv_box)
        while fsh_pos:
            pag.moveTo(fsh_pos[0])
            t.sleep(g(0.15))
            pag.mouseDown(button='right')
            t.sleep(g(0.05))
            pag.mouseUp(button='right')
            t.sleep(g(0.15))
            im = iGrab.grab()
            fsh_pos = match_template(fsh, im, 0.98, inv_box)

def get_brightness(im=None):
    if im == None:
        im = iGrab.grab()

    BRIGHTNESS_TL = 1700,70
    BRIGHTNESS_BR = 2560,400
    BRIGHTNESS_SPEED = 60
    br = 0
    bg = 0
    bb = 0
    samples = 0
    for x in range(BRIGHTNESS_TL[0], BRIGHTNESS_BR[0], BRIGHTNESS_SPEED):
        for y in range(BRIGHTNESS_TL[1], BRIGHTNESS_BR[1], BRIGHTNESS_SPEED):
            px = im.getpixel((x,y))
            br += px[0]
            bg += px[1]
            bb += px[2]
            samples += 1

    bdist = dist((br/samples,bg/samples,bb/samples),(0,0,0))
    if bdist > FULL_BRIGHT:
        return 1.0
    else:
        ret = bdist / FULL_BRIGHT
        return ret

def lerp(x, pts):
    if x < pts[0][0]:
        return pts[0][1]
    for i in range(0,len(pts)-1):
        if pts[i][0] < x < pts[i+1][0]:
            dx = pts[i+1][0] - pts[i][0]
            dy = pts[i+1][1] - pts[i][1]

            dix = x - pts[i][0]
            return pts[i][1] + dy * ( dix/dx )
    return pts[-1][1]
    