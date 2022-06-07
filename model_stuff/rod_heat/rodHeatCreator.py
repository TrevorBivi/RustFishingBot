PROJ_PATH = 'C:\\Users\\Monchy\\Documents\\RustFishingBot\\' #from settings import *

from numpy import loadtxt
from keras.models import Sequential #, load_model
from keras.layers import Dense, Dropout, LayerNormalization, BatchNormalization
from keras.optimizers import Adam
import numpy as np
import random as r
import time as t
import json
#import konverter

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

POINTS_LEN = 9
CUT_TIME = 4.4
TRAIN_PERC = 0.93

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
            frame = [sesh[pos_ind][0] - 1760, sesh[pos_ind][1] - 880, sesh[pos_ind][2] - start_time]
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
model.add(Dropout(0.1))
model.add(Dense((POINTS_LEN * 3 + 3), activation='relu'))
model.add(Dropout(0.1))
model.add(Dense(8, activation='relu'))
model.add(Dropout(0.05))
model.add(Dense(1, activation='relu'))

optimizer = Adam(
    learning_rate=0.00075,
)

model.compile(loss='mean_squared_error', optimizer=optimizer, metrics=['accuracy'])


model.fit(train_data, train_out, epochs=120, batch_size=50, verbose=2)
model.evaluate(test_data, test_out)
#712
#600
#492 2?
#553 4
model.save(".\\model_stuff\\rod_heat\\rod_heat_model_5", save_format='h5')


'''
# make class predictions with the model
predictions = model.predict(test_data)#(model.predict(inp_datas) > 0.5).astype(int)
# summarize the first 5 cases
for i in range(len(test_out)):
    print('%s => %d (expected %d)' % (test_data[i].tolist(), predictions[i], test_out[i]))

model.save(".\\model_stuff\\rod_heat\\rod_heat_model", save_format='h5')

'''
#konverter.konvert(".\\model_stuff\\rod_heat\\rod_heat_model.h5", output_file='examples/test_model')

'''
model_json = model.to_json()
with open('rod_heat.json', 'w+') as json_file:
    json_file.write(model_json)

'''

'''

model2 = RodHeatManager(".\\model_stuff\\rod_heat\\rod_heat_model")
print('test load')
t1 = t.time()
pred1 = model2.predict( [1964.448275862069, 889.2068965517242, 3.946277618408203, 2.510222764723949, 1.1626487641135554, 0.03300046920776367, -8.009315323707597, 2.702142524452711, 0.032997846603393555, -4.350877192982352, 12.526315789473756, 0.03300023078918457, 1.420196833547152, 1.8401797175865795, 0.03300213813781738, -3.182820784729529, 12.627783669141081, 0.017460346221923828, -2.699130434782546, 2.107826086956493, 0.034718990325927734, -5.498064516129034, -3.001935483870966, 0.03200125694274902, -2.4619354838710024, 2.3059354838709396, 0.03299903869628906] )
t2 = t.time()
for i in range(1000):
    pred2 = model2.predict( [1964.448275862069, 889.2068965517242, 3.946277618408203, 2.510222764723949, 1.1626487641135554, 0.03300046920776367, -8.009315323707597, 2.702142524452711, 0.032997846603393555, -4.350877192982352, 12.526315789473756, 0.03300023078918457, 1.420196833547152, 1.8401797175865795, 0.03300213813781738, -3.182820784729529, 12.627783669141081, 0.017460346221923828, -2.699130434782546, 2.107826086956493, 0.034718990325927734, -5.498064516129034, -3.001935483870966, 0.03200125694274902, -2.4619354838710024, 2.3059354838709396, 0.03299903869628906] )
t3 = t.time()
print('time',t2-t2, (t3-t2)/1000, 'test', pred1,  pred2)#43'''
