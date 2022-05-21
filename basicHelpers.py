from settings import *

import ctypes

import cv2
import numpy as np
from PIL import ImageGrab as iGrab

class Line(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.m = (p2[0] - p1[0]) / (p2[1] - p1[1])
        self.b = p1[0] - self.m * p1[1]

    def f(self,x):
        return int(self.m * x + self.b)

def i_x(ratiox):
    return int(SCREEN_SIZE[0] * ratiox)

def r_x(intx):
    return intx / 2560

def i_y(ratioy):
    return int(SCREEN_SIZE[1] * ratioy)

def r_y(inty):
    return inty / 1440

def i_p(ratiopos):
    return i_x(ratiopos[0]), i_y(ratiopos[1])

def r_p(intpos):
    return r_x(intpos[0]), r_y(intpos[1])

def al(*lists):
    return tuple([sum(vals) for vals in zip(*lists)])

MOUSEEVENTF_MOVE = 0x0001 
def wm_mouse_move (x_pos, y_pos,flags=0):
        """generate a mouse event"""
        if x_pos == 0 and y_pos == 0:
            return
        flags = MOUSEEVENTF_MOVE + flags
        x_calc = ctypes.c_long(int(x_pos))
        y_calc = ctypes.c_long(int(y_pos))
        #print('mmove',x_calc,y_calc)
        if not ctypes.windll.user32.mouse_event(flags, x_calc, y_calc, 0, 0):
            print('WWWTTTFF!!!!!!!!!!!\n!!!!!!!!!!!!\n!!!!!!!!!!')
        return 

def g(mn,mx=None,dev=None):
    if mx == None:
        mx = 2 * mn
    return mn

def sdist(rgb1, rgb2 = (0,0,0)):
    return sum([(rgb1[i] - rgb2[i])**2 for i in range(len(rgb1))])

def dist(rgb1,rgb2 = (0,0,0)):
    return sdist(rgb1, rgb2) ** 0.5

def get_template(name):
    #print('rust\\' + IMG_PATH + '\\' +name)
    ret = cv2.imread('rust\\' + IMG_PATH + '\\' +name,cv2.IMREAD_COLOR)
    assert( type(ret) == np.ndarray)
    return ret

def match_template(template, im=None,min_match=-1, box=None,error=False):
    '''returns top left position of best match for image 
    Keyword arguments:
    image -- the image template is inside
    template -- the image to find inside of image
    min_match -- minimum match before fail 0.0-1.0 (default -1.0)
    error -- if fail, raise error instead of return none (default = False)
    '''
    if not im:
        im = iGrab.grab()

    if box:
        #print(type(im), im.shape)
        im = im.crop(box)
        #print(type(im, im.shape))

    image =  cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    #setup mask layer
    mask = None
    if template.shape[2] == 4:
        t_channels = cv2.split(template)
        template = cv2.merge(t_channels[:3])
        mask = cv2.merge([t_channels[3]]*3)

    match = cv2.minMaxLoc(cv2.matchTemplate(image, template ,cv2.TM_CCORR_NORMED,mask=mask))
    if min_match > match[1]:
        if error:
            raise botException("failed to match a template")
        return None

    if box:
        return al(match[3],box[:2]),match[1] 

    return match[3],match[1]
