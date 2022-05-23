from settings import *

import ctypes

import cv2
import numpy as np
from PIL import ImageGrab as iGrab
import math as m

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


#FISH_LEFT_P1 = (-1.6, 0, 2.3)#(-2.3, 0, 6.1)
FISH_LEFT_P2 = (-0.3, 0, 0.5)#(0.3, 0, 6.1)

FOV = 90
PLAYER = (0,1.5,0)
rotation = (0,0,0) # * FOV/2
display_surface = (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, SCREEN_SIZE[0]/2 * 90/108 * 0.95 )# (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, 1) #SCREEN_SIZE[0] / FOV
def persp_proj(pnt, rotation=rotation, player=PLAYER, e=display_surface):
    
    # a =  #(6.5,-1.5,-2.5)
    a = pnt
    c = player
    th = rotation[0]+ m.radians(17.3) , rotation[1]- 1*m.radians(20.9),0#rotation[1]- 1*m.radians(20.9) ,0 

    def c_(i):
        return m.cos(th[i])

    def s_(i):
        return m.sin(th[i])

    X = a[0] - c[0]
    Y = a[1] - c[1]
    Z = a[2] - c[2]

    x = 0
    y = 1
    z = 2

    
    #ax = m.atan2(X,Z) + th[1]
    #ay = -(m.atan2(Y,Z) + th[0])
    #return e[0] + e[2] * ax, e[1] + e[2] * ay

    '''dr1 = np.array([
        (1,0,0),
        (0,c_(x), s_(x)),
        (0,s_(x), c_(x))
    ])

    dr2 = np.array([
        (c_(y), 0, -s_(y)),
        (0, 1, 0),
        (s_(y),0, c_(x)) #+c ?
    ])

    dr3 = np.array([
        (c_(z), s_(z), 0),
        (-s_(z), c_(z), 0),
        (0,0, 1) #+c ?
    ])
    da = np.array(a)
    dc = np.array(c)

    dm = np.multiply( np.multiply( np.multiply( dr1, dr2), dr3), da-dc )
    #dm = dr1.cross(dr2).cross(dr3).dot(da-dc)
    print('DM',dm)'''
    

    '''print('d')
    print([
           [ c_(y)*( s_(z)*Y + c_(z)*X), - s_(y)*Z],
            [s_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)), c_(x)*( c_(z)*Y - s_(z)*X)],
            [c_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)), - s_(x)*( c_(z)*Y - s_(z)*X)]
        ])'''
    
    d = [
            c_(y)*( s_(z)*Y + c_(z)*X) - s_(y)*Z,
            s_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)) + c_(x)*( c_(z)*Y - s_(z)*X),
            c_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)) - s_(x)*( c_(z)*Y - s_(z)*X)
        ]

    '''d = [
            'c_(y)'*( s_(z)*Y + c_(z)*X) - 's_(y)'*Z,
            s_(x)*('c_(y)'*Z + 's_(y)'*( s_(z)*Y + c_(z)*X)) + c_(x)*( c_(z)*Y - s_(z)*X),
            c_(x)*(c_(y)*Z + 's_(y)'*( s_(z)*Y + c_(z)*X)) - s_(x)*( c_(z)*Y - s_(z)*X)
        ]'''
    #d = dm
    bx = e[z]/d[z] * d[x] + e[x]
    by = -(e[z]/d[z] * d[y]) + e[y]
    #print('b\n', bx,by)
    return int(bx),int(by)


def weak_proj(pnt, rotation,player=(0,1.5,0), pxperdeg= 2560/108):
    X = pnt[0] - player[0]
    Y = pnt[1] - player[1]
    Z = pnt[2] - player[2]
    
    rx = m.degrees(m.atan2(X,Z) - rotation[0])
    ry = m.degrees(m.atan2(Y,Z) - rotation[1])
    print('XYZ',X,Y,Z  , 'rrryyy', rx,ry)
    ret = int(rx * pxperdeg) + SCREEN_SIZE[0]//2, - int(ry*pxperdeg) + SCREEN_SIZE[1]//2
    print( int(rx * pxperdeg), int(ry*pxperdeg), 'ret=',ret )
    return ret