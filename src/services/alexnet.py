import sys
from selector import data_selector, model_selector
import keras
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, Flatten, Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.callbacks import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
import numpy as np
from imagenet import load_with_train
from keras.applications import imagenet_utils

if __name__=='__main__':
    argv = sys.argv
    if len(argv) < 2:
        "Usage: python imagenet.py <model_name>"
    model_name = argv[1]
    train_X, train_y, test_X, test_y = load_with_train((227, 227))
    test_X = imagenet_utils.preprocess_input(test_X)
    train_X = imagenet_utils.preprocess_input(train_X)
    
    model = model_selector(model_name, weights=True)
    model.compile(optimizer='sgd', loss='mse',
                  metrics=['accuracy'])
    early_stopping = EarlyStopping(patience=0, verbose=1)
    
    model.fit(train_X, train_y, epochs=30,
                        validation_data=(test_X, test_y), shuffle=True, callbacks=[early_stopping])

    model.save_weights("data/alexnet.h5")
    score = model.evaluate(test_X, test_y)
    print("loss: {}, accuracy: {}".format(score[0], score[1]))
