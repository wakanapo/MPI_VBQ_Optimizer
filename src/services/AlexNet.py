"""
    Model Name:

        AlexNet - using the Functional Keras API

        Replicated from the Caffe Zoo Model Version.

    Paper:

         ImageNet classification with deep convolutional neural networks by Krizhevsky et al. in NIPS 2012

    Alternative Example:

        Available at: http://caffe.berkeleyvision.org/model_zoo.html

        https://github.com/uoguelph-mlrg/theano_alexnet/tree/master/pretrained/alexnet

    Original Dataset:

        ILSVRC 2012

"""
from keras.models import Model, Sequential
from keras.layers import Input, Dense, Dropout, Flatten, Activation
from keras.layers import Convolution2D, MaxPooling2D
from keras.layers.convolutional import ZeroPadding2D
from keras.layers.normalization import BatchNormalization
from KerasLayers.Custom_layers import LRN2D

def create_model():
    DROPOUT = 0.5
    model_input = Input(shape = (227, 227, 3))
    
    # First convolutional Layer (96x11x11)
    z = Convolution2D(filters = 96, kernel_size = (11,11), strides = (4,4),
                      activation = "relu")(model_input)
    z = LRN2D()(z)
    z = MaxPooling2D(pool_size = (3,3), strides=(2,2))(z)
    
    # Second convolutional Layer (256x5x5)
    z = Convolution2D(filters = 256, kernel_size = (5,5), strides = (1,1),
                      activation = "relu", padding='same')(z)
    z = LRN2D()(z)
    z = MaxPooling2D(pool_size = (3,3), strides=(2,2))(z)
    
    # Rest 3 convolutional layers
    z = Convolution2D(filters = 384, kernel_size = (3,3), strides = (1,1),
                      padding='same', activation = "relu")(z)
    
    z = Convolution2D(filters = 384, kernel_size = (3,3), strides = (1,1),
                      padding='same', activation = "relu")(z)
    
    z = Convolution2D(filters = 256, kernel_size = (3,3), strides = (1,1),
                      padding='same', activation = "relu")(z)
    
    z = MaxPooling2D(pool_size = (3,3), strides=(2,2))(z)
    z = Flatten()(z)
    
    z = Dense(4096, activation="relu")(z)
    z = Dropout(DROPOUT)(z)
    
    z = Dense(4096, activation="relu")(z)
    z = Dropout(DROPOUT)(z)
    model_output = Dense(1000, activation="softmax")(z)
    
    model = Model(model_input, model_output)
    return model
