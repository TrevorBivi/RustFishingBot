from settings import *

import ctypes

import cv2
import numpy as np
from PIL import ImageGrab as iGrab
import math as m

class LineIter(object):
    def __init__(self, p1, p2, speed=1, min_x = 0, max_x = SCREEN_SIZE[0], min_y = 0, max_y = SCREEN_SIZE[1], cap_bounds=False):
        self.line = Line(p1,p2)
        self.speed = speed
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.cap_bounds = cap_bounds

        if abs(p2[0] - p1[0]) > abs(p2[1] - p1[1]):
            self.dir = 'x'
            self.min = max(min_x, min(max_x, p1[0]))
            self.max = max(min_x, min(max_x, p2[0]))
        else:
            self.dir = 'y'
            self.min = max(min_y, min(max_y, p1[1]))
            self.max = max(min_y, min(max_y, p2[1]))

        if self.min < self.max:
            self.iter_dir = 1
        else:
            self.iter_dir = -1

        self.cur = self.min

    def __iter__(self):
        return self

    def __next__(self):
        #print('lineiter',self.line.p1, self.line.p2, ' cur', self.cur, 'minmax',self.min, self.max)
        ret = None
        while not ret:
            self.cur += self.iter_dir * self.speed
            if (self.iter_dir > 0 and self.cur >= self.max) or (self.iter_dir < 0 and self.cur <= self.max):
                raise StopIteration
            if self.dir == 'x':
                ret = self.cur,self.line.fox(self.cur)
                if not (self.min_y < ret[1] <self.max_y):
                    ret = None
            else:
                ret = self.line.foy(self.cur),self.cur
                if not (self.min_x < ret[0] < self.max_x):
                    ret = None
        return ret
        
class Line(object):
    def __init__(self, p1, p2 ):
        self.p1 = p1
        self.p2 = p2
        if (p2[0] - p1[0]) == 0:
            self.m = 9999
        else:
            self.m = (p2[1] - p1[1]) / (p2[0] - p1[0])
        self.b = p1[1] - self.m * p1[0]
        
    def foy(self,y):
        return int( (y - self.b)/self.m)

    def fox(self,x):
        return int(self.m * x + self.b)

    def get_iter(self, speed=1, min_x = 0, max_x = SCREEN_SIZE[0], min_y = 0, max_y = SCREEN_SIZE[1]):
        return LineIter(self.p1, self.p2, speed, min_x, max_x, min_y, max_y)

def line_intersection(line1, line2):
    if type(line1) == Line:
        line1 = line1.p1, line1.p2
        line2 = line2.p1, line2.p2
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


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

def ml(list1, list2):
    return list1[0] - list2[0], list1[1]-list2[1]

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

def get_template(name, mode = cv2.IMREAD_COLOR):
    #print('rust\\' + IMG_PATH + '\\' +name)
    ret = cv2.imread('rust\\' + IMG_PATH + '\\' +name, mode)
    print(type(ret))
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
        print('4')
        t_channels = cv2.split(template)
        template = cv2.merge(t_channels[:3])
        mask = cv2.merge([t_channels[3]]*3)

    match = cv2.minMaxLoc(cv2.matchTemplate(image, template ,cv2.TM_CCORR_NORMED,mask=mask))
    if min_match > match[1]:
        if error:
            raise Exception("failed to match a template")
        return None

    if box:
        return al(match[3],box[:2]),match[1] 

    return match[3],match[1]


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

dm = np.dot( np.multiply( np.multiply( dr1, dr2), dr3), da-dc )'''
#dm = dr1.cross(dr2).cross(dr3).dot(da-dc)
#print('DM',dm)


'''print('d')
print([
        [ c_(y)*( s_(z)*Y + c_(z)*X), - s_(y)*Z],
        [s_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)), c_(x)*( c_(z)*Y - s_(z)*X)],
        [c_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)), - s_(x)*( c_(z)*Y - s_(z)*X)]
    ])'''
#d = dm
#print(d)
'''d = [
        'c_(y)'*( s_(z)*Y + c_(z)*X) - 's_(y)'*Z,
        s_(x)*('c_(y)'*Z + 's_(y)'*( s_(z)*Y + c_(z)*X)) + c_(x)*( c_(z)*Y - s_(z)*X),
        c_(x)*(c_(y)*Z + 's_(y)'*( s_(z)*Y + c_(z)*X)) - s_(x)*( c_(z)*Y - s_(z)*X)
    ]'''
#d = dm

#FISH_LEFT_P1 = (-1.6, 0, 2.3)#(-2.3, 0, 6.1)
FISH_LEFT_P2 = (-0.3, 0, 0.5)#(0.3, 0, 6.1)

FOV = 90
PLAYER = (-0.09,1.53,0.19)
rotation = (0,0,0) # * FOV/2
display_surface = (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, SCREEN_SIZE[1]/2 * 44/45 )# (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, 1) #SCREEN_SIZE[0] / FOV
def persp_proj(pnt, rotation=rotation, player=PLAYER, e=display_surface):
    c_x = m.cos(rotation[0])
    c_y = m.cos(rotation[1])
    s_x = m.sin(rotation[0])
    s_y = m.sin(rotation[1])

    X = pnt[0] - player[0]
    Y = pnt[1] - player[1]
    Z = pnt[2] - player[2]

    d = [
            c_y*X - s_y*Z,
            s_x*(c_y*Z + s_y*X) + c_x*Y,
            c_x*(c_y*Z + s_y*X) - s_x*Y
        ]

    bx = e[2]/d[2] * d[0] + e[0]
    by = -(e[2]/d[2] * d[1]) + e[1]

    return int(bx),int(by)

def persp_pnt(bx, by, rotation=rotation, height=0, player=PLAYER, e=display_surface):
    s_x = m.sin(rotation[0])
    c_x = m.cos(rotation[0])
    s_y = m.sin(rotation[1])
    c_y = m.cos(rotation[1])

    cn_x = (bx - e[0])/e[2]
    cn_y = (by - e[1])/e[2]

    x1 = cn_x * s_y * c_x - c_y
    z1 = cn_x * c_y * c_x + s_y
    y1 = -cn_x * s_x

    x2 = cn_y * s_y * c_x + s_x * s_y
    z2 = cn_y * c_x * c_y +  s_x * c_y
    y2 = -cn_y * s_x + c_x

    Y = -player[1] - height
    Z = Y*(y1/x1-y2/x2)/(z2/x2-z1/x1)
    X = Y*(y1/z1-y2/z2)/(x2/z2-x1/z1)

    return X + player[0], height, Z + player[2]

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


#if __name__ == '__main__':
#    persp_pnt()