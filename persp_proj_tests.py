import pygame
import numpy as np
from math import *

from PIL import Image, ImageDraw

width = 2560
height = 1440
angle = 90

from PIL import Image, ImageDraw
#im = Image.new('RGBA', (400, 400), (0, 255, 0, 255)) 
#draw = ImageDraw.Draw(im) 
#draw.line((100,200, 150,300), fill=128)
#im.show()

rr = 0

FAR_LEFT = (-2.3, 0, 6.1)
FAR_RIGHT = ( 0.5, 0 , 6.1)
NEAR_LEFT = (-2.3, 0, 0.1)
NEAR_RIGHT = (0.5, 0, 0.1)

#FAR_LEFT = (-0.5, 0, 6.1)
#FAR_RIGHT = (0.5, 0 , 6.1)
#NEAR_LEFT = (-0.5, 0, 5.1)
#NEAR_RIGHT = (0.5, 0, 5.1)

SCREEN_SIZE = 2560,1440
#SCREEN_SIZE[0]/4
FOV = 90
PLAYER = (0,1.5,0)
rotation = (0,radians(30),0)
display_surface = (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, FOV/2 )# (SCREEN_SIZE[0]/2,SCREEN_SIZE[1]/2, 1) #SCREEN_SIZE[0] / FOV
def persp_proj(pnt, rotation=rotation, player=PLAYER, e=display_surface):
    
    # a =  #(6.5,-1.5,-2.5)
    a = pnt
    c = player
    th = rotation

    def c_(i):
        return cos(th[i])

    def s_(i):
        return sin(th[i])

    X = a[0] - c[0]
    Y = a[1] - c[1]
    Z = a[2] - c[2]

    x = 0
    y = 1
    z = 2

    
    ax = atan2(X,Z) + th[1]
    ay = -(atan2(Y,Z) + th[0])
    #return e[0] + e[2] * ax, e[1] + e[2] * ay

    dr1 = np.array([
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
    print('DM',dm)
    

    print('d')
    print([
           [ c_(y)*( s_(z)*Y + c_(z)*X), - s_(y)*Z],
            [s_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)), c_(x)*( c_(z)*Y - s_(z)*X)],
            [c_(x)*(c_(y)*Z + s_(y)*( s_(z)*Y + c_(z)*X)), - s_(x)*( c_(z)*Y - s_(z)*X)]
        ])
    
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
    print('b\n', bx,by)
    return int(bx),int(by)


for r in (-30,40,10):
    rotation = (0,radians(r),0)
    print("ROT",rotation)
    im = Image.new('RGB',SCREEN_SIZE, color='BLACK')

    pos1 = persp_proj(FAR_LEFT,rotation=rotation)
    pos2 = persp_proj(FAR_RIGHT,rotation=rotation)
    pos3 = persp_proj(NEAR_RIGHT,rotation=rotation)
    pos4 = persp_proj(NEAR_LEFT,rotation=rotation)

    pos1 = pos1[0], pos1[1]
    pos2 = pos2[0], pos2[1]
    pos3 = pos3[0], pos3[1]
    pos4 = pos4[0], pos4[1]

    draw = ImageDraw.Draw(im)
    #draw.line((0,0, 30,70), fill='white')
    draw.line((*pos1, *pos2), fill='white')
    draw.line((*pos2, *pos3), fill='red')
    draw.line((*pos3, *pos4), fill='green')
    draw.line((*pos4, *pos1), fill='blue')

    im.save('dbg\\rot' + str(r) + '.png')

#im.putpixel((0,0), (0,0,255))
#im.putpixel( (im.size[0] - 1, im.size[1] - 1), (0,0,255))

'''
for i, pos in enumerate((pos1, pos2, pos3, pos4)):
    try:
        #im.putpixel((pos), ( int(255 / (i+1)),50*(i+1),0))
    except IndexError:
        pass'''

im.show()


'''
w = 1

aspect_ratio = width / height

fov = 1.0 / tan(angle/2.0)

far = 9999
near = 0.01

clip_matrix = [
        [fov * aspect_ratio, 0, 0, 0],
        [0, fov, 0, 0],
        [0, 0, (far+near)/(far-near), 1],
        [0, 0, (2*far*near)/(near-far), 0]
    ]

new_x = (x*width) / (2 * w) + width/2
new_y = (y*height) / (2 * w) + height/2'''
