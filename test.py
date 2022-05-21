from PIL import ImageGrab as iGrab
import time as t
from PIL import Image
import os
from fishingHelpers import *
from fisher import *

def f():
    ims = []
    for i in range(4):
        t.sleep(1)
        print(i)
    try:
        for i in range(30):
            print(i)
            im = iGrab.grab()
            ims.append(im)
            t.sleep(1)
    except KeyboardInterrupt:
        pass
    
    for i in range(100):
        print(i)
        ims[i].save('dbg/snssappedr_' + str(i)+'.png')


def ts():
    f = Fisher()
    for filename in os.scandir(r'C:\Users\Monchy\Documents\RustFishingBot\dbg'):
        if filename.is_file():
            if 'snapped' in filename.path:
                im = Image.open(filename.path)
                brightness = get_brightness(im)
                
                def rod_snapped():
                    mx = 0
                    mn = 999
                    for x in range(RAISED_ROD_TL[0], RAISED_ROD_BR[0], RAISED_ROD_SPEED):
                        for y in range(RAISED_ROD_TL[1], RAISED_ROD_BR[1], RAISED_ROD_SPEED):
                            #print('raised rod check',x,y, px)
                            px = im.getpixel((x,y))
                            #print('raised rod check',x,y, px)
                            im.putpixel((x,y), (0,255,0))
                            max_chan = LINE_CHANNEL_INTENSITY * brightness ** 1.5
                            mn = min(mn, px[0], px[1], px[2])
                            mx = max(mx, px[0], px[1], px[2])
                            if px[0] < max_chan and px[1] < max_chan and px[2] < max_chan:
                                im.putpixel((x,y), (0,0,255))
                                return 'SNAP', mn, mx
                    return None

                
                
                f.brightness = brightness
                event = rod_snapped()
                print('brightness', brightness, '  event', event, filename)

def b():
    im = iGrab.grab()
    f = Fisher()

    def rod_snapped():
        mx = 0
        mn = 999
        ret = None
        passes = 0
        for x in range(RAISED_ROD_TL[0], RAISED_ROD_BR[0], RAISED_ROD_SPEED):
            for y in range(RAISED_ROD_TL[1], RAISED_ROD_BR[1], RAISED_ROD_SPEED):
                #print('raised rod check',x,y, px)
                px = im.getpixel((x,y))
                #print('raised rod check',x,y, px)
                im.putpixel((x,y), (0,255,0))
                max_chan = LINE_CHANNEL_INTENSITY * f.brightness ** 1.5
                mn = min(mn, px[0], px[1], px[2])
                mx = max(mx, px[0], px[1], px[2])
                if px[0] < max_chan and px[1] < max_chan and px[2] < max_chan:
                    im.putpixel((x,y), (0,0,255))
                    passes += 1
                    if ret == None:
                        ret = 'SNAP', mn, mx
        print('passes', passes)
        return ret
                
    while True:
        im = iGrab.grab()
        print(get_brightness(im))
        f.brightness = get_brightness(im)
        print(f.event_check(im))
        rod_snapped()
