import logging
from keras.applications import vgg16
import cifar10
import imagenet
import mnist
import AlexNet
import numpy as np
import h5py
import pickle

logger = logging.getLogger("Selector")

class ModelMock:
    def get_weights(self):
        return []

def data_selector(model_name):
    if model_name == 'vgg_like' or model_name == 'hinton':
        _, _, val_X, val_y = cifar10.read_data()
    elif model_name == 'vgg16' :
        val_X, val_y = imagenet.load()
        val_X = vgg16.preprocess_input(val_X)
    elif model_name == 'alexnet':
        val_X, val_y = imagenet.load(size=(227, 227))
        val_X = vgg16.preprocess_input(val_X)
    elif model_name == 'mnist':
        _, _, val_X, val_y = mnist.read_data()
    else:
        val_X = []
        val_y = []
    return val_X, val_y

def model_selector(model_name, weights=False):
    model = ModelMock()
    if model_name == 'vgg_like' or model_name == 'hinton':
        if model_name == 'vgg_like':
            model_class = cifar10.Vgg_like();
            logger.debug("Model: vgg_like")
        else:
            model_class = cifar10.Hinton();
            logger.debug("Model: hinton")
        model = model_class.build((32, 32, 3))
        if weights:
            model.load_weights('data/'+model_class.name+'.h5')
            logger.debug("Load weights: success.")
    else:
        if model_name == 'vgg16':
            logger.debug("Model: vgg16")
            if weights:
                model = vgg16.VGG16(weights='data/vgg16_retraining.h5')
                logger.debug("Load weights: success.")
            else:
                model = vgg16.VGG16(weights=None)
        elif model_name == 'alexnet':
            logger.debug("Model: alexnet")
            if weights:
                model = AlexNet.create_model()
                with open('data/alexnet.pkl', 'rb') as f:
                    weights = pickle.load(f)
                model.set_weights(weights)
                logger.debug("Load weights: success")
            else:
                model = AlexNet.create_model()
        elif model_name == 'mnist':
            model_class = mnist.Mnist();
            logger.debug("Model: MNIST")
            model = model_class.build()
            if weights:
                model.load_weights('data/'+model_class.name+'.h5')
                logger.debug("Load weights: success.")
    return model


