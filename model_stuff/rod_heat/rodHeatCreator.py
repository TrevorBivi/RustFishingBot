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
TRAIN_PERC = 0.98

inp_datas = []
out_datas = []
seshs = {}
with open(PROJ_PATH + 'dbg\\snapsv3.txt', 'r') as ff:
    dat = ff.read()
    for s in dat.split('\n'):
        if len(s) > 16:
            obj = json.loads(s)
            sesh = obj[1]
            if len(sesh) < 16:
                print("BAD SESH")
                continue
            for dat in sesh:
                if 'xy' in dat and type(dat['xy'][0]) == list:
                    dat['xy'] = dat['xy'][0]
            seshs[obj[0]] = sesh

#r.shuffle(seshs)
test_train_split = round(len(seshs) * TRAIN_PERC)




def get_frames(sesh_dict):
    datas = []
    outs = []

    start_heat = 0
    avg_first = 0
    avg_second = 0
    smp_first = 0
    smp_second = 0

    for sesh_name, sesh in sesh_dict.items():
        if len(sesh) < POINTS_LEN + 6:
            continue
        #print(sesh[0])
        start_i = 0
        for sesh_i in range(1,len(sesh)):
            if 'cl' in sesh[sesh_i-1].keys() and not 'cl' in sesh[sesh_i]:
                start_i = sesh_i
        if start_i != 0:
            sesh = sesh[start_i:]
        
        new_sesh = []
        for dat in sesh:
            if 'xy' in dat:
                new_sesh.append(dat)
        sesh=new_sesh
            
        if len(sesh) < POINTS_LEN+2:
            continue


        start_time = sesh[0]['tm']
        rec_end = sesh[-1]['tm']

        end_index = None
        end_time = None
        for pos_ind, dat in enumerate(sesh):
            if dat['tm'] > rec_end - CUT_TIME:
                end_index = pos_ind
                end_time = sesh[pos_ind]['tm']
                break
        else:
            continue


        if start_i != 0:
            smp_second += 1
            avg_second += end_time - start_time
            if end_time - start_time < 2.4:
                start_heat = min(20, 30 * (2.4 - (end_time - start_time)) )
                print('TIME',sesh_name,end_time - start_time, start_heat)
        else:
            smp_first += 1
            avg_first += end_time - start_time


        for pos_ind in range(POINTS_LEN, end_index):
            frame = [sesh[pos_ind]['xy'][0] - 1760, sesh[pos_ind]['xy'][1] - 880, sesh[pos_ind]['tm'] - start_time]
            for samp_ind in range(0, POINTS_LEN, 1):
                samp = sesh[pos_ind -samp_ind-1]
                next_samp = sesh[pos_ind -samp_ind]
                dx = next_samp['xy'][0] - samp['xy'][0]
                dy = next_samp['xy'][1] - samp['xy'][1]
                dt = next_samp['tm'] - samp['tm']
                frame.append(dx)
                frame.append(dy)
                frame.append(dt)
            datas.append(frame)
            outs.append(start_heat + (100-start_heat) * (sesh[pos_ind]['tm'] - start_time) / (end_time - start_time))

    c = list(zip(datas, outs))
    r.shuffle(c)
    datas, outs = zip(*c)
    print('ANVERAGE!!!!!!!!!!!!!!',avg_first/smp_first, avg_second/smp_second)
    return datas, outs

sesh_names = list(seshs.keys())
r.shuffle(sesh_names)
train_amnt = round(TRAIN_PERC * len(sesh_names))
train_sesh_names = sesh_names[:train_amnt]
test_sesh_names = sesh_names[train_amnt:]

train_seshs = {}
for name in train_sesh_names:
    train_seshs[name] = seshs[name]

test_seshs = {}
for name in test_sesh_names:
    test_seshs[name] = seshs[name]



train_data, train_out = get_frames(train_seshs)

print('TRAIN OUT', len(train_out))
test_data, test_out = get_frames(test_seshs)



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
model.add(Dropout(0.14))
model.add(Dense((POINTS_LEN * 3 + 3), activation='relu'))
model.add(Dropout(0.14))
model.add(Dense(8, activation='relu'))
model.add(Dropout(0.08))
model.add(Dense(1, activation='relu'))

optimizer = Adam(
    learning_rate=0.00075,
)

model.compile(loss='mean_squared_error', optimizer=optimizer)


model.fit(train_data, train_out, epochs=190, batch_size=50, verbose=2)
model.evaluate(test_data, test_out)
#712
#600
#492 2?
#553 4
path = ".\\model_stuff\\rod_heat\\"
name = input('name>')

numpy_layers = []

for layer in model.layers:
    conf = layer.get_config()
    
    if 'activation' in conf:
        numpy_layers.append(layer.get_weights())

with open(path+name+'.pickle', 'wb+') as handle:
    pickle.dump(numpy_layers, handle)

model.save(path+name, save_format='h5')

raise Exception('stop')
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
