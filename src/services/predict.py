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

def predict(genoms, model_name, val_X, val_y):
    model = model_selector(model_name, weights=True)
    g_W = model.get_weights()
    W_q = copy.deepcopy(g_W)
    W_q[::2] = [converter(genoms[i].gene)(W_q[i*2]) for i in range(len(W_q)//2)]
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
        layer_idx = int(d.split('_')[2])
        if os.path.isdir(path+d):
            dirs.append((layer_idx, path+d))
    return dirs

if __name__=='__main__':
    argv = sys.argv
    if len(argv) < 3:
        print("Please set model name and genom file name.")
        exit()
    dirname = argv[1]
    model_name = argv[2]
    val_X, val_y = data_selector(model_name)
    print("data load: success.")
    dirs = get_dir(dirname)
    genoms = [[]]*len(dirs)
    for d in dirs:
        genoms[d[0]] = (get_best_genom(d[1]))
    accuracy = predict(genoms, model_name, val_X, val_y)
    print("acc: {}".format(accuracy))
