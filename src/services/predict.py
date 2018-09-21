import copy
import numpy as np
import sys
sys.path.append('src/protos/')
import genom_pb2
import os
from keras.applications import vgg16, resnet50
from keras import backend as K
from keras import optimizers
import numpy as np
import tensorflow as tf

import cifar10
import imagenet
from genom_evaluation_server import data_selector, model_selector, converter

def read_genom(filename):
    generation = genom_pb2.Generation()
    try:
        with open(filename, 'rb') as f:
            generation.ParseFromString(f.read())
    except IOError:
        print('Could not open file.')
    return generation

def get_best_genom(dirname):
    generation = read_genom(dirname+'/generation199.pb')
    arr = np.asarray([g.evaluation for g in generation.individuals])
    arr = np.argsort(arr)[::-1]
    return generation.individuals[arr[0]].genom

def predict(genom, model_name, val_X, val_y):
    model = model_selector(model_name, weights=True)
    g_W = model.get_weights()
    W_q = list(map(converter(genom.gene), copy.deepcopy(g_W)))
    print("quantize: success.")
    model.set_weights(W_q)
    model.compile(optimizer=optimizers.Adam(),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    score = model.evaluate(val_X, val_y, verbose=0)
    return score[1]

def get_dir(dirname):
    path = 'data/{}/'.format(dirname)
    dirs = []
    for d in os.listdir(path):
        if os.path.isdir(path+d):
            dirs.append(path+d)
    return sorted(dirs)

if __name__=='__main__':
    argv = sys.argv
    if len(argv) < 3:
        print("Please set model name and genom file name.")
        exit()
    dirname = argv[1]
    model_name = argv[2]
    val_X, val_y = data_selector(model_name)
    dataset = [[(5000, 10000)], [(0, 2500), (7500, 10000)], [(0, 5000)],
               [(2500, 7500)], [(2500, 5000), (7500, 10000)],
               [(0, 2500), (5000, 7500)]]
    print("data load: success.")
    X = np.array([])
    y = np.array([])
    for d in get_dir(dirname):
        for d2 in os.listdir(d):
            path = d + "/" + d2
            if os.path.isdir(path):
                ds = dataset[int(d2[-12])]
                for i in range(len(ds)):
                    p = ds[i]
                    if i == 0:
                        X = val_X[p[0]:p[1]]
                        y = val_y[p[0]:p[1]]
                    else:
                        X = np.vstack((X, val_X[p[0]:p[1]]))
                        y = np.vstack((y, val_y[p[0]:p[1]]))
                accuracy = predict(get_best_genom(path), model_name, X, y)
                print(path, "acc: {}".format(accuracy))
