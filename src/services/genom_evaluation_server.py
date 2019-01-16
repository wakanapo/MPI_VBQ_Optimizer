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
from converter import converter, quantize
from imagenet import AlexNet
import gc
from keras import Model
from keras.layers import Lambda

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
val_X = []
val_y = []
g_W = []

fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='data/python_server_log.txt', filemode='w',
                    format=fmt, level=logging.DEBUG)
logger = logging.getLogger('Main')

def calculate_fitness(genoms, model_name, quantize_layer):
    try:
        if model_name == 'alexnet':
            W_q = np.load(open("data/bvlc_alexnet.npy", "rb"), encoding="latin1").item()
            if len(genoms.genom) > 1:
                for i in range(8):
                    W_q[AlexNet.layers[i]][0] = converter(genoms.genom[i].gene)(W_q[AlexNet.layers[i]][0])
            elif quantize_layer == -1:
                for i in range(8):
                    W_q[AlexNet.layers[i]][0] = converter(genoms.genom[0].gene)(W_q[AlexNet.layers[i]][0])
            elif quantize_layer >= 0 and quantize_layer*2 < len(W_q):
                W_q[AlexNet.layers[quantize_layer]][0] = converter(genoms.genom[0].gene)(W_q[AlexNet.layers[quantize_layer]][0])
            else:
                sys.exit("quantize_layer is out of index.")
            accuracy = AlexNet.alexnet(W_q, val_X, val_y)
            gc.collect()
            return accuracy
        else:
            with K.get_session().graph.as_default():
                model = model_selector(model_name)
#                 W_q = copy.deepcopy(g_W)
#                 if len(genoms.genom) > 1:
#                     W_q[::2] = [converter(genoms.genom[i].gene)(W_q[i*2]) for i in range(len(W_q)//2)]
#                 elif quantize_layer == -1:
#                     W_q[::2] = list(map(converter(genoms.genom[0].gene), W_q[::2]))
#                 elif quantize_layer >= 0 and quantize_layer*2 < len(W_q):
#                     W_q[quantize_layer*2] = converter(genoms.genom[0].gene)(W_q[quantize_layer*2])
#                 else:
#                     sys.exit("quantize_layer is out of index.")
#                 model.set_weights(W_q)
                layers = [l for l in model.layers]
                layer_ids = [1, 2, 4, 5, 7, 8, 9, 11, 12, 13, 15, 16, 17, 20, 21, 22]
                x = layers[0].output
                j = 0
                for i in range(1, len(layers)):
                    if quantize_layer == -1:
                        if i in layer_ids:
                            x = Lambda(quantize(genoms.genom[j].gene))(x)
                            j += 1
                    else:
                        if i == layer_ids[quantize_layer]:
                            x = Lambda(quantize(genoms.genom[0].gene))(x)
                    x = layers[i](x)
                model = Model(input=layers[0].input, output=x)
                logger.debug(model.summary)
                model.set_weights(g_W)
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
        return genom_pb2.Individual(genoms=request,
                                    evaluation=calculate_fitness(request,
                                                                 self.model_name_,
                                                                 self.quantize_layer_))

    def GetIndividualMock(self, request, context):
        return genom_pb2.Individual(genoms=request, evaluation=0.5)


def server(model_name, quantize_layer, rank):
    global val_X, val_y, g_W
    val_X, val_y = data_selector(model_name)
    logger.debug("data load: success.")
    if model_name != "alexnet":
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
