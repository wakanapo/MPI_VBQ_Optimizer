import numpy as np
import keras.backend as K

def converter(rep_v):
    rep_v = np.array(rep_v)
    def f(arr):
        arr = np.array(arr)
        partition = np.array([(rep_v[i] + rep_v[i+1]) / 2 for i in range(len(rep_v)-1)])
        end_idx = len(partition) - 1
        for i in range(end_idx):
            arr[(arr > partition[i]) & (arr <= partition[i+1])] = rep_v[i+1]
        arr[arr <= partition[0]] = rep_v[0]
        arr[arr > partition[end_idx]] = rep_v[end_idx+1]
        return arr
    return f

def quantize(rep_v):
    rep_v = np.array(rep_v)
    def f(arr):
        partition = np.array([(rep_v[i] + rep_v[i+1]) / 2 for i in range(len(rep_v)-1)])
        end_idx = len(partition) - 1
        for i in range(end_idx):
            target = K.cast(K.equal(K.greater(arr, partition[i]), K.less_equal(arr, partition[i+1])), K.floatx())
            arr = arr*(1 - target) + rep_v[i+1]*target
        target = K.cast(K.less_equal(arr, partition[0]), K.floatx())
        arr = arr*(1-target) + rep_v[0]*target
        target = K.cast(K.greater(arr, partition[end_idx]), K.floatx())
        arr = arr*(1-target) + rep_v[end_idx+1]*target
        return arr
    return f

if __name__=="__main__":
    from keras.models import Model
    from keras.layers import Input, Lambda
    rep_v = np.array([-2, -1, 0, 1, 2])
    arr = np.array([-2.5, -1.2, 0.2, 1.4, 1.9, 3.5]).reshape((1, 3, 2))
    x_in = Input(shape=(3, 2))
    x = Lambda(quantize(rep_v))(x_in)
    model = Model(input=x_in, output=x)
    result = model.predict(arr)
    print("actual: ", result.flatten())
    print("expect: ", [-2, -1, 0, 1, 2, 2])
