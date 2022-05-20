P1440 = (2560, 1440)
P1080 = (1920, 1080)
SCREEN_SIZE = P1440
SENSITIVITY = 4.5
assert (SCREEN_SIZE in [P1080, P1440])
import time as t
MAX_ROT = 50
MIN_ROT = -10

DBG_DEPTH = 1

dbg_time = t.time()

def dbg(msg, depth=0):
    global dbg_time
    if depth >= DBG_DEPTH:
        new_time = t.time()
        print('(',new_time - dbg_time, ') ', msg)
        dbg_time = new_time

class Line(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.m = (p2[0] - p1[0]) / (p2[1] - p1[1])
        self.b = p1[0] - self.m * p1[1]

    def f(self,x):
        return int(self.m * x + self.b)

if SCREEN_SIZE == P1440:
    
    BP_POS = 882,762
    HOT_POS = 883,1281
    SLOT_SIZE = 128
    IMG_PATH = '1440p_quality2'
    HP_OFFSET = 4, 128
    FULL_OFFSET = 16,12

    PULLING_TL = 1940, 840
    PULLING_BR = 2000, 900
    PULLING_SCAN_SPEED = 7
    
    FISH_LEFT_PLAYER = (1139,1439)
    FISH_LEFT_WALL_MIN = (942,1000)
    FISH_LEFT_WALL_MAX = (827, 893)
    
    FISH_LEFT_SPEED = 2

    RAISED_ROD_TL = 2450,645
    RAISED_ROD_BR = 2560,824
    RAISED_ROD_SPEED = 12

    #FISH_RIGHT_LINE_START

    #WATER_START = 500
    #NEAR_START = 950
    #SCAN_SPEED_NEAR = 8
    #SCAN_SPEED_FAR = 4
    #HUD_START_X = 2144
    
    STATUS_0_POS = (2447, 1217)
    STATUS_HEIGHT = 56
    
else:
    BP_POS = 660, 573
    HOT_POS = 661,963
    SLOT_SIZE = 96
    IMG_PATH = '1080p_quality0'
    HP_OFFSET = 3, 96
    FULL_OFFSET = 12,9

    PULLING_TL = 1460-50,654-50
    PULLING_BR = 1460+50- 14, 654+50
    PULLING_SCAN_SPEED = 7

    FISH_LEFT_PLAYER = (800,1079)
    FISH_LEFT_WALL_MIN = (740,740)
    FISH_LEFT_WALL_MAX = (545, 645)

    FISH_LEFT_SPEED = 2

    RAISED_ROD_TL = 1853,479
    RAISED_ROD_BR = 1920,600
    RAISED_ROD_SPEED = 25


    STATUS_0_POS = (1839, 910)
    STATUS_HEIGHT = 39

defaultVar = {
    #'FOCUS_LINE': Line((2560//2,1440),(769,753)),
    'MSPEED': 2,
    #'PSPEED': 5,
    'COOLTIME': 0.8,
    'HEATTIME': 0.7,
    'SIDEHEATTIME': 0.3,
    
    'MAXWAIT': 40,
    'SCANTIME': 0.2,

    'MAX_ROT': 50,
    'MIN_ROT':-10,
    
    #'STARTHEAT': -0.1,
    'FIRST_PULL_TIME': 1.8,
    'FIRST_COOL_TIME': 1.8,

    'FISHES_PER_ITER':16
}