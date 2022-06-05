if 1:
    import os
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'


from keras.models import load_model
import numpy as np
class RodHeatManager:
    def __init__(self,path):
        self.path = path
        self.model = load_model(path)
        '''with open(path, 'r') as json_file:
            string = json_file.read()
            self.model = model_from_json(string)'''
    
    def predict(self, data):
        in_data = np.array([data])
        out_data = self.model(in_data)
        return out_data[0].numpy()[0]