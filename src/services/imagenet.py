import re
import os
import scipy.io
import numpy as np
from keras.preprocessing.image import img_to_array, load_img
from keras.utils import np_utils
from tqdm import tqdm
import pickle
import tensorflow as tf
import time
import logging

logger = logging.getLogger("DataLoder")

def load(size=(224, 224)):
    gt_lines = open("data/ILSVRC2012/val.txt", 'r').readlines()
    gt_pairs = [line.split() for line in gt_lines[40000:41000]]
    print("Data: {}".format(len(gt_pairs)))
    logger.debug("Data: {}".format(len(gt_pairs)))
#     gt_pairs = [line.split() for line in gt_lines[5000:7000]]
    image_paths = [os.path.join("data/ILSVRC2012/val/", p[0]) for p in gt_pairs]
    labels = np.array([int(p[1]) for p in gt_pairs])
    labels = np.identity(1000)[labels]
    imgs = []
    for img_path in tqdm(image_paths):
        img = img_to_array(load_img(img_path, target_size=size))
        imgs.append(img)
    imgs = np.array(imgs)
    return imgs, labels

def load_test(size=(224, 224)):
    gt_lines = open("data/ILSVRC2012/val.txt", 'r').readlines()
    gt_pairs = [line.split() for line in gt_lines[:5000]]
    image_paths = [os.path.join("data/ILSVRC2012/val/", p[0]) for p in gt_pairs]
    labels = np.array([int(p[1]) for p in gt_pairs])
    labels = np.identity(1000)[labels]
    imgs = []
    for img_path in tqdm(image_paths):
        img = img_to_array(load_img(img_path, target_size=size))
        imgs.append(img)
    imgs = np.array(imgs)
    return imgs, labels


def load_with_train(size=(224, 224)):
    with open("data/ILSVRC2012/imagenet_val_labels_for_keras.pkl", 'rb') as f:
        labels = pickle.load(f)
    test_labels = np.identity(1000)[labels[:5000]]
    train_labels = np.identity(1000)[labels[5000:25000]]
    
    test_imgs = []
    train_imgs = []
    for i in tqdm(range(len(test_labels))):
        picture_name = "data/ILSVRC2012/val/ILSVRC2012_val_000{0:05d}.JPEG".format(i+1)
        test_img = img_to_array(load_img(picture_name, target_size=size))
        test_imgs.append(test_img)
    for i in tqdm(range(len(train_labels))):
        picture_name = "data/ILSVRC2012/val/ILSVRC2012_val_000{0:05d}.JPEG".format(i+1)
        train_img = img_to_array(load_img(picture_name, target_size=size))
        train_imgs.append(train_img)
    test_imgs = np.asarray(test_imgs)
    train_imgs = np.asarray(train_imgs)
    return train_imgs, train_labels, test_imgs, test_labels

class AlexNet:
    layers = ["conv1", "conv2", "conv3", "conv4", "conv5", "fc6", "fc7", "fc8"]
    
    @staticmethod
    def alexnet(net_data, val_X, val_y):
        def conv(x, kernel, biases, k_h, k_w, c_o, s_h, s_w,  padding="VALID", group=1):
            '''From https://github.com/ethereon/caffe-tensorflow
            '''
            c_i = x.get_shape()[-1]
            assert c_i%group==0
            assert c_o%group==0
            convolve = lambda i, k: tf.nn.conv2d(i, k, [1, s_h, s_w, 1], padding=padding)
            
            
            if group==1:
                conv = convolve(x, kernel)
            else:
                input_groups =  tf.split(x, group, 3)   #tf.split(3, group, input)
                kernel_groups = tf.split(kernel, group, 3)  #tf.split(3, group, kernel) 
                output_groups = [convolve(i, k) for i,k in zip(input_groups, kernel_groups)]
                conv = tf.concat(output_groups, 3)          #tf.concat(3, output_groups)
            return  tf.reshape(tf.nn.bias_add(conv, biases), [-1]+conv.get_shape().as_list()[1:])
        
        
        
        x = tf.placeholder(tf.float32, [None, 227, 227, 3])
        y_ = tf.placeholder(tf.float32, [None, 1000])
    
        #conv1
        #conv(11, 11, 96, 4, 4, padding='VALID', name='conv1')
        k_h = 11; k_w = 11; c_o = 96; s_h = 4; s_w = 4
        conv1W = tf.Variable(net_data["conv1"][0])
        conv1b = tf.Variable(net_data["conv1"][1])
        conv1_in = conv(x, conv1W, conv1b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=1)
        conv1 = tf.nn.relu(conv1_in)
        
        #lrn1
        #lrn(2, 2e-05, 0.75, name='norm1')
        radius = 2; alpha = 2e-05; beta = 0.75; bias = 1.0
        lrn1 = tf.nn.local_response_normalization(conv1,
                                                  depth_radius=radius,
                                                  alpha=alpha,
                                                  beta=beta,
                                                  bias=bias)
    
        #maxpool1
        #max_pool(3, 3, 2, 2, padding='VALID', name='pool1')
        k_h = 3; k_w = 3; s_h = 2; s_w = 2; padding = 'VALID'
        maxpool1 = tf.nn.max_pool(lrn1, ksize=[1, k_h, k_w, 1], strides=[1, s_h, s_w, 1], padding=padding)
        
        
        #conv2
        #conv(5, 5, 256, 1, 1, group=2, name='conv2')
        k_h = 5; k_w = 5; c_o = 256; s_h = 1; s_w = 1; group = 2
        conv2W = tf.Variable(net_data["conv2"][0])
        conv2b = tf.Variable(net_data["conv2"][1])
        conv2_in = conv(maxpool1, conv2W, conv2b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
        conv2 = tf.nn.relu(conv2_in)
        
        
        #lrn2
        #lrn(2, 2e-05, 0.75, name='norm2')
        radius = 2; alpha = 2e-05; beta = 0.75; bias = 1.0
        lrn2 = tf.nn.local_response_normalization(conv2,
                                                  depth_radius=radius,
                                                  alpha=alpha,
                                                  beta=beta,
                                                  bias=bias)
        
        #maxpool2
        #max_pool(3, 3, 2, 2, padding='VALID', name='pool2')                                                  
        k_h = 3; k_w = 3; s_h = 2; s_w = 2; padding = 'VALID'
        maxpool2 = tf.nn.max_pool(lrn2, ksize=[1, k_h, k_w, 1], strides=[1, s_h, s_w, 1], padding=padding)
        
        #conv3
        #conv(3, 3, 384, 1, 1, name='conv3')
        k_h = 3; k_w = 3; c_o = 384; s_h = 1; s_w = 1; group = 1
        conv3W = tf.Variable(net_data["conv3"][0])
        conv3b = tf.Variable(net_data["conv3"][1])
        conv3_in = conv(maxpool2, conv3W, conv3b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
        conv3 = tf.nn.relu(conv3_in)
        
        #conv4
        #conv(3, 3, 384, 1, 1, group=2, name='conv4')
        k_h = 3; k_w = 3; c_o = 384; s_h = 1; s_w = 1; group = 2
        conv4W = tf.Variable(net_data["conv4"][0])
        conv4b = tf.Variable(net_data["conv4"][1])
        conv4_in = conv(conv3, conv4W, conv4b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
        conv4 = tf.nn.relu(conv4_in)
        
        #conv5
        #conv(3, 3, 256, 1, 1, group=2, name='conv5')
        k_h = 3; k_w = 3; c_o = 256; s_h = 1; s_w = 1; group = 2
        conv5W = tf.Variable(net_data["conv5"][0])
        conv5b = tf.Variable(net_data["conv5"][1])
        conv5_in = conv(conv4, conv5W, conv5b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
        conv5 = tf.nn.relu(conv5_in)
        
        #maxpool5
        #max_pool(3, 3, 2, 2, padding='VALID', name='pool5')
        k_h = 3; k_w = 3; s_h = 2; s_w = 2; padding = 'VALID'
        maxpool5 = tf.nn.max_pool(conv5, ksize=[1, k_h, k_w, 1], strides=[1, s_h, s_w, 1], padding=padding)
        
        #fc6
        #fc(4096, name='fc6')
        fc6W = tf.Variable(net_data["fc6"][0])
        fc6b = tf.Variable(net_data["fc6"][1])
        fc6 = tf.nn.relu_layer(tf.reshape(maxpool5, [-1, int(np.prod(maxpool5.get_shape()[1:]))]), fc6W, fc6b)
        
        #fc7
        #fc(4096, name='fc7')
        fc7W = tf.Variable(net_data["fc7"][0])
        fc7b = tf.Variable(net_data["fc7"][1])
        fc7 = tf.nn.relu_layer(fc6, fc7W, fc7b)
        
        #fc8
        #fc(1000, relu=False, name='fc8')
        fc8W = tf.Variable(net_data["fc8"][0])
        fc8b = tf.Variable(net_data["fc8"][1])
        fc8 = tf.nn.xw_plus_b(fc7, fc8W, fc8b)
        
        #prob
        #softmax(name='prob'))
        y = tf.nn.softmax(fc8)
        
        correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        init = tf.global_variables_initializer()
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        sess = tf.Session(config=config)
        sess.run(init)
        
        t = time.time()
        output = sess.run(accuracy, feed_dict = {x:val_X, y_:val_y})
        sess.close()
        tf.reset_default_graph()
        return output
