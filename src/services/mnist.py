from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop
from keras import utils

from cifar10 import Model

class Mnist(Model):
    def __init__(self):
        self.name = "mnist"

    def build(self):
        model = Sequential()
        model.add(Dense(512, activation='relu', input_shape=(784,)))
        model.add(Dropout(0.2))
        model.add(Dense(512, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(10, activation='softmax'))
        return model

def read_data():
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    y_train = utils.to_categorical(y_train, 10)
    y_test = utils.to_categorical(y_test, 10)
    x_train = x_train.reshape(60000, 784)
    x_test = x_test.reshape(10000, 784)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255
    return x_train, y_train, x_test, y_test

def run(my_model):
    x_train, y_train, x_test, y_test = read_data()

    model = my_model.build()
    model.summary()
    model.compile(loss='categorical_crossentropy', optimizer=RMSprop(),
                  metrics=['accuracy'])
    model.fit(x_train, y_train, batch_size=128, epochs=15,
              validation_data=(x_test, y_test), shuffle=True)

    model.save_weights("data/" + my_model.name + ".h5")
    scores = model.evaluate(x_test, y_test, verbose=1)
    print('Test loss:', scores[0])
    print('Test accuracy:', scores[1])

if __name__ == '__main__':
    run(Mnist())
