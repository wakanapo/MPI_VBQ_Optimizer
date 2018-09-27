from keras.applications import vgg16, resnet50
import cifar10
import imagenet

def data_selector(model_name):
    if model_name == 'vgg_like' or model_name == 'hinton':
        _, _, val_X, val_y = cifar10.read_data()
    else:
        val_X, val_y = imagenet.load()
        if model_name == 'vgg16':
            val_X = vgg16.preprocess_input(val_X)
        elif model_name == 'resnet50':
            val_X = resnet50.preprocess_input(val_X)
    return val_X, val_y

def model_selector(model_name, weights=True):
    model = None
    if model_name == 'vgg_like' or model_name == 'hinton':
        if model_name == 'vgg_like':
            model_class = cifar10.Vgg_like();
            print("Model: vgg_like")
        else:
            model_class = cifar10.Hinton();
            print("Model: hinton")
        model = model_class.build((32, 32, 3))
        if weights:
            model.load_weights('data/'+model_class.name+'.h5')
            print("load weights: success.")
    else:
        if model_name == 'vgg16':
            print("Model: vgg16")
            if weights:
                model = vgg16.VGG16(weights='data/vgg16_retraining.h5')
                print("load weights: success.")
            else:
                model = vgg16.VGG16(weights=None)
        elif model_name == 'resnet50':
            print("Model: resnet50")
            if weights:
                model = resnet50.ResNet50(weights='data/resnet50_retraining.h5')
                print("load weights: success")
            else:
                model = resnet50.ResNet50(weights=None)
    return model
