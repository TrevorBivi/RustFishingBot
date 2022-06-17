import time

import cv2

import mss
import numpy


from tkinter import *

master = Tk()
w1 = Scale(master, from_=0, to=255.0, orient=HORIZONTAL)
w1.pack()
w2 = Scale(master, from_=0, to=255.0, orient=HORIZONTAL)
w2.pack()
w3 = Scale(master, from_=0, to=255.0, length=512, orient=HORIZONTAL)
w3.pack()

rgb_min = 0,0,0
rgb_max = 73,77,82
rgb_cur = 21,21,30


## 66, 71, 75
###.6, .5, .56


###0, 01, 04
## 0 , 0, .35

###07,06,14
##.24,.23,.32   - .15

###21,21,30
##.25 .18 .34

###48,46,47
##.65,.46,.43

###68,72,77
##.65,.47,.49

###73,77,82
##.62,.49,.47


xs=[
    [0,1,4],
    [7,6,14],
    [21,21,30],
    [48,46,47],
    [68,72,77],
    [73,77,82],
]

ys = [
    .35,
    .32,
    .34,
    .43,
    .48,
    .48,
]


###22,23,31
##.10,.07,.12

###32,28,58
##.03,.03,04


###20, 21, 28
##.12,.07,.09
##.15,.12,.16


#(70,74,77)
#36
#43
#47

#(52,50,51)
#27
#30

#(20,20,28)
#6


#(0,1,4)
#1

xs = [
(70,74,77),
(70,74,77),
(52,50,51),
(20,20,28),
(0,1,4)
]

ys = [
    45,
    38,
    28.5,
    6,
    1
]


linexs = [
    (0,0,0),
    (6,5,12),
    (6,5,12),
    (21,21,28),
    (21,21,28),
    (71,75,79),
    (71,75,79),
]

lineys = [
    5.25,
    17,
    23, #17
    26,
    42, #26,
    47,
    105
]


if 1:
    import pandas
    from sklearn import linear_model

    
    regr = linear_model.LinearRegression()
    regr.fit(linexs, lineys)
    print(regr.coef_, regr.intercept_)

    predictedCO2 = regr.predict([(0,0,0), (6,5,12), (21,21,28), (71,75,79),])
    print(predictedCO2)
    raise Exception('stop')


def is_band(pxl, rgb_brightness, mults):
    pxl = [pxl[2], pxl[1], pxl[0]]


    #print(rgb_brightness, rgb_max, mults)
    return any([
        mults[i] > pxl[i] for i in range(3)
    ])


def scan_pxls(img):
    rgb_brightness = [rgb_cur[i]/rgb_max[i] for i in range(3)]
    mults = w1.get(),w2.get(),w3.get()
    for x in range(0,2560//2,3):
        master.update()
        for y in range(0,1440//2,3):
            pxl = img[y][x]
            if not is_band(pxl, rgb_brightness, mults):
                img[y][x] = [255,255,255    ,255]

def screen_record_efficient():
    # 800x600 windowed mode
    mon = {"top": 1440//2, "left": 2560//2, "width": 2560//2, "height": 1440//2}

    title = "[MSS] FPS benchmark"
    fps = 0
    sct = mss.mss()
    last_time = time.time()

    while True:
        img = numpy.asarray(sct.grab(mon))
        master.update()
        fps += 1
        scan_pxls(img)
        cv2.imshow(title, img)
        if cv2.waitKey(25) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break
        master.update()

    return fps

if 0:
    import pyautogui as pag
    from PIL import ImageGrab
    input('top_left')
    tl = pag.position()
    input('bot right')
    br = pag.position()
    
    im = ImageGrab.grab(bbox=(tl[0],tl[1], br[0] - tl[0], br[1] - tl[1]))
    print(tl,br, im.size)
    im.show()

    
    r = 0
    g = 0
    b = 0
    for x in range(im.size[0]):
        for y in range(im.size[1]):
            pxl = im.getpixel((x,y))
            r += pxl[0]
            g += pxl[1]
            b += pxl[2]
    ar = im.size[0] * im.size[1]
    print(r/ar, g/ar, b/ar)

time.sleep(1)
#print("PIL:", screen_record())
print("MSS:", screen_record_efficient())
