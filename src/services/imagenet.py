import re
import os
import scipy.io
import numpy as np
from keras.preprocessing.image import img_to_array, load_img
from keras.utils import np_utils
from tqdm import tqdm
import pickle

def load():
    with open("data/ILSVRC2012/imagenet_val_labels_for_keras.pkl", 'rb') as f:
        labels = pickle.load(f)
    labels = np.identity(1000)[labels[:5000]]
    
    imgs = []
    for i in tqdm(range(len(labels))):
        picture_name = "data/ILSVRC2012/val/ILSVRC2012_val_000{0:05d}.JPEG".format(i+1)
        img = img_to_array(load_img(picture_name, target_size=(224, 224)))
        imgs.append(img)
    imgs = np.asarray(imgs)
    return imgs, labels
