from abc import ABCMeta, abstractmethod
from keras import utils
from keras import optimizers
from keras.datasets import cifar10
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, Conv2D, MaxPooling2D, BatchNormalization
from keras.callbacks import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator


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
        model.add(Conv2D(64, (3, 3), padding='same', activation='relu', input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling2D(pool_size=(2, 2)))
        
        model.add(Conv2D(128, (3, 3), padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(Conv2D(128, (3, 3), padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling2D(pool_size=(2, 2)))
        
        model.add(Conv2D(256, (3, 3), padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(Conv2D(256, (3, 3), padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(Conv2D(256, (3, 3), padding='same', activation='relu'))
        model.add(BatchNormalization())
        model.add(Conv2D(256, (3, 3), padding='same', activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        
        model.add(Flatten())
        model.add(Dense(1024, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(512, activation='relu'))
        model.add(BatchNormalization())
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
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=False,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        rotation_range=15,  # randomly rotate images in the range (degrees, 0 to 180)
        width_shift_range=0.1,  # randomly shift images horizontally (fraction of total width)
        height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False)  # randomly flip images
        # (std, mean, and principal components if ZCA whitening is applied).
    datagen.fit(x_train)
    
    model = my_model.build(x_train.shape[1:])
    model.summary()
    model.compile(loss='categorical_crossentropy', optimizer=optimizers.SGD(lr=0.01, momentum=0.9, decay=5e-4),
                  metrics=['accuracy'])
    early_stopping = EarlyStopping(patience=0, verbose=1)
    
    model.fit_generator(datagen.flow(x_train, y_train, batch_size=64), steps_per_epoch=x_train.shape[0] // 64, epochs=30,
              validation_data=(x_test, y_test), shuffle=True)
#              callbacks=[early_stopping])

    model.save_weights("data/" + my_model.name + ".h5")
    scores = model.evaluate(x_test, y_test, verbose=1)
    print('Test loss:', scores[0])
    print('Test accuracy:', scores[1])

if __name__ == '__main__':
    run(Vgg_like())
