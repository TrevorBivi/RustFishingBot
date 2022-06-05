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

POINTS_LEN = 6
CUT_TIME = 4.4
TRAIN_PERC = 0.982

inp_datas = []
out_datas = []
seshs = []
with open(PROJ_PATH + 'dbg\\snapUsed.txt', 'r') as ff:
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


model.fit(train_data, train_out, epochs=100, batch_size=50, verbose=2)
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
pred1 = model2.predict( [1982.7719298245613, 873.5263157894736, 3.6030290126800537, 7.692283806862179, 0.1900326036329716, 0.032633304595947266, -2.2318293921368877, -1.3030610764543553, 0.03200125694274902, -1.6091595107989178, 3.520296643247434, 0.03399991989135742, 1.9206349206349387, 7.1535303776682895, 0.034403085708618164, 1.4959349593495972, 7.599663582842709, 0.03173255920410156, 4.923419879360154, 0.22069236821403138, 0.03466033935546875] )
t2 = t.time()
for i in range(1000):
    pred2 = model2.predict( [1982.7719298245613, 873.5263157894736, 3.6030290126800537, 7.692283806862179, 0.1900326036329716, 0.032633304595947266, -2.2318293921368877, -1.3030610764543553, 0.03200125694274902, -1.6091595107989178, 3.520296643247434, 0.03399991989135742, 1.9206349206349387, 7.1535303776682895, -0.034403085708618164, 1.4959349593495972, 7.599663582842709, -0.03173255920410156, 4.923419879360154, 0.22069236821403138, -0.03466033935546875] )
t3 = t.time()
print('time',t2-t2, (t3-t2)/1000, 'test', pred1,  pred2)#43
