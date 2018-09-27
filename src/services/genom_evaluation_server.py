import copy
from concurrent import futures
import time
import os
pwd = os.getcwd()
import sys
sys.path.append(pwd+'/src/protos')
import genom_pb2
import genom_pb2_grpc
import grpc
from keras import backend as K
from keras import optimizers
import numpy as np
import tensorflow as tf

from selector import data_selector, model_selector
from converter import converter

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
val_X = []
val_y = []
g_W = []

def calculate_fitness(genom, model_name, quantize_layer):
    with K.get_session().graph.as_default():
        print("start evaluation!")
        model = model_selector(model_name, weights=False)
        W_q = copy.deepcopy(g_W)
        if quantize_layer == -1:
            W_q[::2] = list(map(converter(genom.gene), W_q[::2]))
        elif quantize_layer*2 < len(W_q):
            W_q[quantize_layer*2] = converter(genom.gene)(W_q[quantize_layer*2])
        else:
            sys.stderr.write("quantize_layer is out of index.")
            exit(1)
        print("quantize: success.")
        model.set_weights(W_q)
        model.compile(optimizer=optimizers.Adam(),
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])
        score = model.evaluate(val_X, val_y, verbose=0)
    K.clear_session()
    return score[1]

class GenomEvaluationServicer(genom_pb2_grpc.GenomEvaluationServicer):
    def __init__(self, genom_name, quantize_layer):
        self.genom_name_ = genom_name
        self.quantize_layer_ = quantize_layer
        
    def GetIndividual(self, request, context):
        return genom_pb2.Individual(genom=request,
                                    evaluation=calculate_fitness(request,
                                                                 self.genom_name_, self.quantize_layer_))

def server(model_name, quantize_layer):
    global val_X, val_y, g_W
    val_X, val_y = data_selector(model_name)
    print("data load: success.")
    model = model_selector(model_name, weights=True)
    g_W = model.get_weights()
    print("model load: success.")
    server = grpc.server(futures.ThreadPoolExecutor())
    genom_pb2_grpc.add_GenomEvaluationServicer_to_server(
        GenomEvaluationServicer(model_name, quantize_layer), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server Ready")
    sys.stdout.flush()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__=='__main__':
    argv = sys.argv
    if len(argv) < 3:
        print("Please set model name and quantize layer.")
        exit()
    server(argv[1], int(argv[2]))
