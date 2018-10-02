import copy
import sys
import numpy as np
from selector import model_selector, data_selector
#from converter import converter

def converter(partition):
    def f(arr):
        arr = np.asarray(arr)
        end_idx = len(partition) - 1
        for i in range(end_idx):
            arr[(arr > partition[i]) & (arr <= partition[i+1])] = (partition[i] + partition[i + 1]) /  2
        arr[arr <= partition[0]] = partition[0]
        arr[arr > partition[end_idx]] = partition[end_idx]
        return arr
    return f

class Predict:
    def __init__(self, model_name):
        self.test_X, self.test_y = data_selector(model_name)
        self.model = model_selector(model_name, weights=True)
        self.g_W = self.model.get_weights()

    def run(self, partition, quantize_layer):
        W_q = copy.deepcopy(self.g_W)
        if quantize_layer == -1:
            W_q[::2] = list(map(converter(partition), W_q[::2]))
        elif quantize_layer >= 0 and quantize_layer*2 < len(W_q):
            W_q[quantize_layer*2] = converter(partition)(W_q[quantize_layer*2])
        else:
            sys.exit("quantize_layer is out of index.")
        self.model.set_weights(W_q)
        self.model.compile(optimizer=optimizers.Adam(),
                        loss='categorical_crossentropy',
                        metrics=['accuracy'])
        score = self.model.evaluate(self.test_X, self.test_y, verbose=0)
        return score[1]

def get_partition_from_abcd(p_num, a, b, c, d):
    x = np.arange(p_num) / p_num
    def f(x):
        return np.sign(x-d) * b * (np.power(a, np.abs(x-d)) - 1) + c
    y = f(x)
    return y
    

if __name__=='__main__':
    argv = sys.argv
    if len(argv) < 4:
        print("Usage: pythono predict_with_abcd.py <model_name> <abcd_file> <partition_num>")
    predict = Predict(argv[1])
    with open(argv[2], 'r') as f:
        lines = f.readlines()
    for line in lines:
        data = list(map(float, line.split(',')))
        partition = get_partition_from_abcd(int(argv[3]), data[1], data[2],
                                            data[3], data[4])
        q_layer = int(data[0])
        acc = predict.run(partition, q_layer)
        print("Layer {}: {}".format(q_layer, acc))
