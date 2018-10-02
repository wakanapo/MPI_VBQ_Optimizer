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
import logging
from selector import data_selector, model_selector
from converter import converter

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
val_X = []
val_y = []
g_W = []

# Logging設定
fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='data/python_server_log.txt', filemode='w',
                    format=fmt, level=logging.DEBUG)
logger = logging.getLogger('Main')

def calculate_fitness(genom, model_name, quantize_layer):
    try:
        with K.get_session().graph.as_default():
            model = model_selector(model_name)
            W_q = copy.deepcopy(g_W)
            if quantize_layer == -1:
                W_q[::2] = list(map(converter(genom.gene), W_q[::2]))
            elif quantize_layer >= 0 and quantize_layer*2 < len(W_q):
                W_q[quantize_layer*2] = converter(genom.gene)(W_q[quantize_layer*2])
            else:
                sys.exit("quantize_layer is out of index.")
            model.set_weights(W_q)
            model.compile(optimizer=optimizers.Adam(),
                          loss='categorical_crossentropy',
                          metrics=['accuracy'])
            score = model.evaluate(val_X, val_y, verbose=0)
        K.clear_session()
        return score[1]
    except:
        logger.exception(sys.exc_info()[0])
        return -1

class GenomEvaluationServicer(genom_pb2_grpc.GenomEvaluationServicer):
    def __init__(self, model_name, quantize_layer):
        self.model_name_ = model_name
        self.quantize_layer_ = quantize_layer
        
    def GetIndividual(self, request, context):
        return genom_pb2.Individual(genom=request,
                                    evaluation=calculate_fitness(request,
                                                                 self.model_name_,
                                                                 self.quantize_layer_))

def server(model_name, quantize_layer, rank):
    global val_X, val_y, g_W
    val_X, val_y = data_selector(model_name)
    logger.debug("data load: success.")
    model = model_selector(model_name, weights=True)
    g_W = model.get_weights()
    logger.debug("model load: success.")
    server = grpc.server(futures.ThreadPoolExecutor())
    genom_pb2_grpc.add_GenomEvaluationServicer_to_server(
        GenomEvaluationServicer(model_name, quantize_layer), server)
    port = 50050 + rank % 4
    server.add_insecure_port('[::]:'+str(port))
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
    if len(argv) < 4:
        sys.exit("Please set model name, quantize layer and rank.")
    os.environ['CUDA_VISIBLE_DEVICES'] = str(int(argv[3]) % 4);
    server(argv[1], int(argv[2]), int(argv[3]))
