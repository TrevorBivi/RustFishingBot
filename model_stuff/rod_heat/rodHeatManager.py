from threading import Thread
import time as t
import pickle

'''
if 1:
    import os
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from keras.models import load_model
'''

import numpy as np

def relu(Z):
    return np.maximum(0,Z)

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

        
    def run(self):
        #print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def predict(model, data):
    if model == None or data == None:
        raise Exception('todo')
    in_data = np.array([data])
    out_data = model(in_data, training=False)
    return out_data[0].numpy()[0]

class RodHeatManager:
    def __init__(self,path):
        self.path = path
        '''
        self.thread = None
        self.model = load_model(path)
        self.numpy_layers = []

        for layer in self.model.layers:
            conf = layer.get_config()
            
            if 'activation' in conf:
                self.numpy_layers.append(layer.get_weights())
        '''

        '''
        file = open('.\\model_stuff\\rod_heat\\rod_heat_layer.obj', 'wb+')
        pickle.load(self.numpy_layers, file)
        file.close()
        '''
        file = open('.\\model_stuff\\rod_heat\\rod_heat_layer.obj', 'rb+')
        self.numpy_layers = pickle.load(file)
        file.close()
        
        print('0000000000000000000000000')
        print(self.numpy_layers[2][1].shape)

        print('0000000000000000000000000')
        
    def thread_predict(self, data):
        self.thread = ThreadWithReturnValue(target=predict, args=(self.model, data))
        self.thread.start()
        return None

    def numpy_predict(self,data):
        layers_in = np.array(data[:])
        
        for weights in self.numpy_layers:
            layers_out = []
            for node_i in range(weights[1].shape[0]):
                new_weight = sum(weights[0][:,node_i] * layers_in) + weights[1][node_i]
                layers_out.append(max(0,new_weight))
            layers_in = layers_out
        return layers_out[0]

    def thread_get(self):
        if self.thread == None or self.thread.is_alive():
            return None
        else:
            ret = self.thread.join()
        self.thread = None
        return ret
        
    def predict(self, data):
        return predict(self.model, data)

if __name__ == '__main__':
    pp = [1964.448275862069-1760, 889.2068965517242-880, 3.946277618408203, 2.510222764723949, 1.1626487641135554, 0.03300046920776367, -8.009315323707597, 2.702142524452711, 0.032997846603393555, -4.350877192982352, 12.526315789473756, 0.03300023078918457, 1.420196833547152, 1.8401797175865795, 0.03300213813781738, -3.182820784729529, 12.627783669141081, 0.017460346221923828, -2.699130434782546, 2.107826086956493, 0.034718990325927734, -5.498064516129034, -3.001935483870966, 0.03200125694274902, -2.4619354838710024, 2.3059354838709396, 0.03299903869628906]
    
    rr = RodHeatManager('.\\rod_heat_modelJun5')
    t1 = t.time()
    for i in range(10):
        pass#rr.predict(pp)
    t2 = t.time()
    for i in range(10):
        rr.numpy_predict(pp)
    t3 = t.time()
    print('times',t2-t1, t3-t2)
