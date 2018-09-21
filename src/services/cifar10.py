from abc import ABCMeta, abstractmethod
from keras import utils
from keras import optimizers
from keras.datasets import cifar10
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, Conv2D, MaxPooling2D
from keras.callbacks import EarlyStopping

class Model(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass
        
    @abstractmethod
    def build(self, input_shape):
        pass
        

class Hinton(Model):
    def __init__(self):
        self.name = "hinton"
        
    def build(self, input_shape):
        model = Sequential()
        model.add(Conv2D(64, (5, 5), padding='same', input_shape=input_shape))
        model.add(MaxPooling2D(pool_size=(3,3), strides=2))
        model.add(Conv2D(64, (5, 5), padding='same'))
        model.add(MaxPooling2D(pool_size=(3, 3), strides=2))
        model.add(Conv2D(64, (5, 5), padding='same'))
        model.add(MaxPooling2D(pool_size=(3, 3), strides=2))
        model.add(Flatten())
        model.add(Dense(10))
        model.add(Activation('sigmoid'))
        return model

class Vgg_like(Model):
    def __init__(self):
        self.name = "vgg_like"
        
    def build(self, input_shape):
        model = Sequential()
        model.add(Conv2D(64, (3, 3), padding='same', input_shape=input_shape))
        model.add(Activation('relu'))
        model.add(Conv2D(64, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        
        model.add(Conv2D(128, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(Conv2D(128, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        
        model.add(Conv2D(256, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(Conv2D(256, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(Conv2D(256, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        
        model.add(Flatten())
        model.add(Dense(1024))
        model.add(Activation('relu'))
        model.add(Dense(512))
        model.add(Activation('relu'))
        model.add(Dense(10))
        model.add(Activation('sigmoid'))
        return model

def read_data():
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    y_train = utils.to_categorical(y_train, 10)
    y_test = utils.to_categorical(y_test, 10)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255
    return x_train, y_train, x_test, y_test

def run(my_model):
    x_train, y_train, x_test, y_test = read_data()
    
    model = my_model.build(x_train.shape[1:])
    model.summary()
    model.compile(loss='categorical_crossentropy', optimizer=optimizers.Adam(),
                  metrics=['accuracy'])
    early_stopping = EarlyStopping(patience=0, verbose=1)
    
    model.fit(x_train, y_train, batch_size=100, epochs=30,
              validation_data=(x_test, y_test), shuffle=True,
              callbacks=[early_stopping])

    model.save_weights("data/" + my_model.name + ".h5")
    scores = model.evaluate(x_test, y_test, verbose=1)
    print('Test loss:', scores[0])
    print('Test accuracy:', scores[1])

if __name__ == '__main__':
    run(Vgg_like())
