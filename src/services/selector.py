import logging
from keras.applications import vgg16, resnet50
import cifar10
import imagenet
import mnist

logger = logging.getLogger("Selector")

class ModelMock:
    def get_weights(self):
        return []

def data_selector(model_name):
    if model_name == 'vgg_like' or model_name == 'hinton':
        _, _, val_X, val_y = cifar10.read_data()
    elif model_name == 'vgg16' or model_name == 'resnet50':
        val_X, val_y = imagenet.load()
        if model_name == 'vgg16':
            val_X = vgg16.preprocess_input(val_X)
        else:
            val_X = resnet50.preprocess_input(val_X)
    elif model_name == 'mnist':
        _, _, val_X, val_y = mnist.read_data()
    else:
        val_X = []
        val_y = []
    return val_X, val_y

def model_selector(model_name, weights=True):
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
        elif model_name == 'resnet50':
            logger.debug("Model: resnet50")
            if weights:
                model = resnet50.ResNet50(weights='data/resnet50_retraining.h5')
                logger.debug("Load weights: success")
            else:
                model = resnet50.ResNet50(weights=None)
        elif model_name == 'mnist':
            model_class = mnist.Mnist();
            logger.debug("Model: MNIST")
            model = model_class.build()
            if weights:
                model.load_weights('data/'+model_class.name+'.h5')
                logger.debug("Load weights: success.")
    return model
