PROJ_PATH = 'C:\\Users\\Monchy\\Documents\\RustFishingBot\\' #from settings import *

from numpy import loadtxt
from keras.models import Sequential #, load_model
from keras.layers import Dense, Dropout, LayerNormalization, BatchNormalization
from keras.optimizers import Adam
import numpy as np
import random as r
import time as t
import json
#from tensorflow.keras.models import load_model
# load the dataset
import pandas as pd
#with open
#POINTS_LEN = 9

from rodHeatManager import *

#class

catch_points = []
catch_dict = {}
rec_times = []
rec_lens = []

POINTS_LEN = 7
CUT_TIME = 4.4
TRAIN_PERC = 0.982

inp_datas = []
out_datas = []
seshs = []
with open(PROJ_PATH + 'dbg\\snapUsed2.txt', 'r') as ff:
    dat = ff.read()
    for s in dat.split('\n'):
        if len(s) > 16:
            sesh = json.loads(s)[1]
            if len(sesh) < 16:
                print("BAD SESH")
                continue
            seshs.append(sesh)

r.shuffle(seshs)
test_train_split = round(len(seshs) * TRAIN_PERC)


def get_frames(sesh_list):
    datas = []
    outs = []
    for sesh in sesh_list:
        if len(sesh) < POINTS_LEN + 6:
            continue
        print(sesh[0])
        start_time = sesh[0][2]
        rec_end = sesh[-1][2]

        end_index = None
        end_time = None
        for pos_ind, pos in enumerate(sesh):
            if pos[2] > rec_end - CUT_TIME:
                end_index = pos_ind
                end_time = sesh[pos_ind][2]
                break
        else:
            continue

        for pos_ind in range(POINTS_LEN, end_index):
            frame = [sesh[pos_ind][0], sesh[pos_ind][1], sesh[pos_ind][2] - start_time]
            for samp_ind in range(0, POINTS_LEN, 1):
                samp = sesh[pos_ind -samp_ind-1]
                next_samp = sesh[pos_ind -samp_ind]
                dx = next_samp[0] - samp[0]
                dy = next_samp[1] - samp[1]
                dt = next_samp[2] - samp[2]
                frame.append(dx)
                frame.append(dy)
                frame.append(dt)
            datas.append(frame)
            outs.append(100 * (sesh[pos_ind][2] - start_time) / (end_time - start_time))

    c = list(zip(datas, outs))
    r.shuffle(c)
    datas, outs = zip(*c)

    return datas, outs



train_data, train_out = get_frames(seshs[:test_train_split])
test_data, test_out = get_frames(seshs[test_train_split:])

#print( [i for i in zip(train_data, train_out)][:10])
#raise Exception('stop')

train_data = np.array(train_data)
train_out = np.array(train_out)
test_data = np.array(test_data)
test_out = np.array(test_out)


model = Sequential()


model.add(Dense(POINTS_LEN * 3 + 3, input_dim=(POINTS_LEN * 3 + 3), activation='relu'))
#model.add(BatchNormalization())
#model.add(Dense((POINTS_LEN + 1)*2, activation='relu'))
model.add(Dropout(0.075))
model.add(Dense((POINTS_LEN * 3 + 3), activation='relu'))
model.add(Dropout(0.075))
model.add(Dense(1, activation='relu'))

optimizer = Adam(
    learning_rate=0.00075,
)

model.compile(loss='mean_squared_error', optimizer=optimizer, metrics=['accuracy'])


model.fit(train_data, train_out, epochs=250, batch_size=50, verbose=2)
# make class predictions with the model
predictions = model.predict(test_data)#(model.predict(inp_datas) > 0.5).astype(int)
# summarize the first 5 cases
for i in range(len(test_out)):
    print('%s => %d (expected %d)' % (test_data[i].tolist(), predictions[i], test_out[i]))

model.save(".\\model_stuff\\rod_heat\\rod_heat_model")
'''
model_json = model.to_json()
with open('rod_heat.json', 'w+') as json_file:
    json_file.write(model_json)'''


model2 = RodHeatManager(".\\model_stuff\\rod_heat\\rod_heat_model")
print('test load')
t1 = t.time()
pred1 = model2.predict( [1920.8902439024391, 827.0975609756098, 2.585576295852661, 0.023577235772563654, 1.8042276422764871, 0.017002582550048828, -19.19826839826851, -8.291082251082344, 0.032507896423339844, 10.680319680319599, 0.07159507159508394, 0.03399968147277832, -13.404858299595162, -5.697705802968926, 0.03400135040283203, -5.6893995552259184, -16.38102297998512, 0.031999826431274414, -9.056338028169193, -7.830985915492988, 0.016999244689941406, -2.229494614747182, -5.224523612261805, 0.03300189971923828] )
t2 = t.time()
for i in range(1000):
    pred2 = model2.predict( [1920.8902439024391, 827.0975609756098, 2.585576295852661, 0.023577235772563654, 1.8042276422764871, 0.017002582550048828, -19.19826839826851, -8.291082251082344, 0.032507896423339844, 10.680319680319599, 0.07159507159508394, 0.03399968147277832, -13.404858299595162, -5.697705802968926, 0.03400135040283203, -5.6893995552259184, -16.38102297998512, 0.031999826431274414, -9.056338028169193, -7.830985915492988, 0.016999244689941406, -2.229494614747182, -5.224523612261805, 0.03300189971923828] )
t3 = t.time()
print('time',t2-t2, (t3-t2)/1000, 'test', pred1,  pred2)#43
