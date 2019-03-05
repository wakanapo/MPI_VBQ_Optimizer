import copy
import sys
import numpy as np
from selector import model_selector, data_selector
from keras import optimizers
from converter import converter
import pickle
import logging
import imagenet
import keras.backend as K
from keras.applications import vgg16

# def converter(partition):
#     def f(arr):
#         arr = np.asarray(arr)
#         end_idx = len(partition) - 1
#         for i in range(end_idx):
#             arr[(arr > partition[i]) & (arr <= partition[i+1])] = (partition[i] + partition[i + 1]) /  2
#         arr[arr <= partition[0]] = partition[0]
#         arr[arr > partition[end_idx]] = partition[end_idx]
#         return arr
#     return f
fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='data/prediction_log.txt', filemode='w',
                    format=fmt, level=logging.DEBUG)
logger = logging.getLogger('Main')

class Predict:
    def __init__(self, model_name, val_X, val_y, g_W):
        self.val_X, self.val_y = val_X, val_y
        self.g_W = g_W
        self.model_name = model_name

    def run(self, partitions, quantize_layer):
        if self.model_name == 'alexnet':
            W_q = np.load(open("data/bvlc_alexnet.npy", "rb"), encoding="latin1").item()
            if len(partitions) > 1:
                for i in range(8):
                    W_q[AlexNet.layers[i]][0] = converter(partitions[i])(W_q[AlexNet.layers[i]][0])
            elif quantize_layer == -1:
                for i in range(8):
                    W_q[AlexNet.layers[i]][0] = converter(partitions[0])(W_q[AlexNet.layers[i]][0])
            elif quantize_layer >= 0 and quantize_layer*2 < len(W_q):
                W_q[AlexNet.layers[quantize_layer]][0] = converter(partitions[0])(W_q[AlexNet.layers[quantize_layer]][0])
            else:
                sys.exit("quantize_layer is out of index.")
            accuracy = AlexNet.alexnet(W_q, self.val_X, self.val_y)
            gc.collect()
            return accuracy
        else:
            with K.get_session().graph.as_default():
                model = model_selector(self.model_name)
                W_q = copy.deepcopy(self.g_W)
                if len(partitions) > 1:
                    W_q[::2] = [converter(partitions[i])(W_q[i*2]) for i in range(len(W_q)//2)]
                elif quantize_layer == -1:
                    W_q[::2] = list(map(converter(partitions[0]), W_q[::2]))
                elif quantize_layer >= 0 and quantize_layer*2 < len(W_q):
                    W_q[quantize_layer*2] = converter(partitions[0])(W_q[quantize_layer*2])
                else:
                    sys.exit("quantize_layer is out of index.")
                model.set_weights(W_q)
                model.compile(optimizer=optimizers.Adam(),
                              loss='categorical_crossentropy',
                              metrics=['accuracy', 'top_k_categorical_accuracy'])
                score = model.evaluate(self.val_X, self.val_y, verbose=0)
            K.clear_session()
            return score
        
def get_partition_from_abcd(p_num, a, b, c, d):
    x = np.arange(p_num) / p_num
    def f(x):
        return np.sign(x-d) * b * (np.power(a, np.abs(x-d)) - 1) + c
    y = f(x)
    return y

def get_partition_from_ab(p_num, a, b):
    x = np.arange(p_num) - (p_num - 1) / 2
    return np.sign(x) * float(b) * (np.power(float(a), np.abs(x)) - 1)

def get_ab(filename):
    with open(filename, 'r') as f:
        line = f.readlines()[-1]
    a, b = line.split(',')
    return a, b

def save(filepath, ab, acc):
    with open(filepath+"/prediction.txt", 'w') as f:
        for i, v in enumerate(ab):
            f.write("Layer{}: (a, b) = ({}, {})\n".format(i, v[0], v[1]))
        f.write("==============\n")
        f.write(str(acc[1])+"\n")
        f.write(str(acc[2])+"\n")

if __name__=='__main__':
    argv = sys.argv
    if len(argv) < 4:
        print("Usage: python predict_with_abcd.py <model_name> <ab_file> <partition_num>")
    model_name = argv[1]
    if model_name == 'alexnet':
        size = (227, 227)
        g_W = []
        layers_n = 8
    else:
        size = (224, 224)
        model = model_selector(model_name, weights=True)
        g_W = model.get_weights()
        layers_n = 16
    val_X, val_y = imagenet.load_test(size)
    val_X = vgg16.preprocess_input(val_X)
    predict = Predict(model_name, val_X, val_y, g_W)
    n = int(argv[3])
    path = argv[2]
    partitions = []
    ab_list = []
    for i in range(layers_n):
        a, b = get_ab(path+"/layer{}.csv".format(i))
        ab_list.append((float(a), float(b)))
        partitions.append(get_partition_from_ab(n, a, b))
    acc = predict.run(partitions, -1)
    print("Top-1 Accuracy: ", acc[1])
    print("Top-5 Accuracy: ", acc[2])
    save(path, ab_list, acc)
