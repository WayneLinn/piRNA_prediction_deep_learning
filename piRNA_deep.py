# Author: Weiran Lin

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys
import tempfile

import piRNA_datasets as input_data

import tensorflow as tf

FLAGS = None

def deepnn(x):

    # Reshape to use within a convolutional neural net.
    # Last dimension is for "features" - there is only one here, since images are gray scale.
    # It would be 3 for an RGB image, 4 for RGBA, etc.
    # TODO(Lin): try at least three combinations of arguments
    with tf.name_scope('reshape'):
        # x_image = tf.reshape(x, [-1, 5, 35, 2])
        
        # x_image = tf.reshape(x, [-1, 1, 175, 1]) # feasible
        
        x_image = tf.reshape(x, [-1, 1, 35, 5])

    # First convolutional layer - maps one grayscale image to 32 feature maps
    # The first two dimensions are the patch size, the next is the number of input channels and the last is the number of output channels.
    # TODO(Lin): Modify with reshape()
    with tf.name_scope('conv1'):
        # W_conv1 = weight_variable([1, 5, 2, 8])
        # b_conv1 = bias_variable([8])
        
        # W_conv1 = weight_variable([1, 15, 1, 32])
        # b_conv1 = bias_variable([32])
        
        W_conv1 = weight_variable([1, 8, 5, 16])
        b_conv1 = bias_variable([16])

        h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)

    # Pooling layer - downsamples by 2X
    with tf.name_scope('pool1'):
        # h_pool1 = max_pool_2x2(h_conv1)
        h_pool1 = max_pool_1x2(h_conv1)

    # Second convolutional layer - maps 32 feature maps to 64.
    # TODO(Lin): Modify with conv1
    with tf.name_scope('conv2'):
        # W_conv2 = weight_variable([1, 5, 8, 16])
        # b_conv2 = bias_variable([16])
        
        # W_conv2 = weight_variable([1, 15, 32, 64])
        # b_conv2 = bias_variable([64])

        W_conv2 = weight_variable([1, 8, 16, 32])
        b_conv2 = bias_variable([32])

        h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)

    # Second pooling layer.
    with tf.name_scope('pool2'):
        # h_pool2 = max_pool_2x2(h_conv2)
        h_pool2 = max_pool_1x2(h_conv2)

    # Fully connected layer 1 -- after 2 round of downsampling, our 28x28 image is down to 7x7x64 maps -- maps this to 1024 features
    # TODO(Lin): Change this (why 1152? the change of dimension must be handled)
    with tf.name_scope('fc1'):
        # W_fc1 = weight_variable([16 * 9, 32])
        # b_fc1 = bias_variable([32])
        
        # W_fc1 = weight_variable([64*44, 1024])
        # b_fc1 = bias_variable([1024])

        W_fc1 = weight_variable([32*9, 256])
        b_fc1 = bias_variable([256])
        
        # h_pool2_flat = tf.reshape(h_pool2, [-1, 16*9])
        # h_pool2_flat = tf.reshape(h_pool2, [-1, 64*44])
        h_pool2_flat = tf.reshape(h_pool2, [-1, 32*9])

        h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

    # Dropout - controls the complexity of the model, prevents co-adaptation of features
    with tf.name_scope('dropout'):
        keep_prob = tf.placeholder(tf.float32)
        h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

    # Map the 1024 features to 10 classes, one for each digit
    with tf.name_scope('fc2'):
        # W_fc2 = weight_variable([32,2])
        # b_fc2 = bias_variable([2])
        
        # W_fc2 = weight_variable([1024,2])
        # b_fc2 = bias_variable([2])
        
        W_fc2 = weight_variable([256,2])
        b_fc2 = bias_variable([2])

        y_conv = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)
    return y_conv, keep_prob

def conv2d(x, W):
    """ conv2d returns a 2d convolution layer with full stride."""
    return tf.nn.conv2d(x, W, strides = [1,1,1,1], padding='SAME')

def max_pool_2x2(x):
    """ max_pool_2x2 downsamples a feature map by 2X."""
    return tf.nn.max_pool(x, ksize=[1,2,2,1], strides=[1,2,2,1], padding='SAME')

def max_pool_1x2(x):
    return tf.nn.max_pool(x, ksize=[1,1,2,1], strides=[1,1,2,1], padding='SAME')

def weight_variable(shape):
    """ weight_variable generates a weight variable of a given shape."""
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    """ bias_variable generates a bias variable of a given shape."""
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

def main(_):
    # Import data
    piRNA = input_data.read_data_sets()

    # Create the model
    x = tf.placeholder(tf.float32, [None, 175])

    # Define loss and optimizer
    y_ = tf.placeholder(tf.float32, [None, 2])

    # Build the graph for the deep net
    y_conv, keep_prob = deepnn(x)

    with tf.name_scope('loss'):
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y_conv)
    cross_entropy = tf.reduce_mean(cross_entropy)

    with tf.name_scope('adam_optimizer'):
        train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
    
    with tf.name_scope('accuracy'):
        correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y_, 1))
        correct_prediction = tf.cast(correct_prediction, tf.float32)
    accuracy = tf.reduce_mean(correct_prediction)

    graph_location = tempfile.mkdtemp()
    print('Saving graph to: %s' % graph_location)
    train_writer = tf.summary.FileWriter(graph_location)
    train_writer.add_graph(tf.get_default_graph())

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for i in range(1000000):
            batch = piRNA.train.next_batch(50)
            # print(batch[0].shape)
            # print(batch[1])
            if i % 50 == 0:
                # train_accuracy = accuracy.eval(feed_dict={x: piRNA.test.images, y_:piRNA.test.labels, keep_prob: 1.0})
                train_accuracy = accuracy.eval(feed_dict={x: batch[0], y_: batch[1], keep_prob: 1.0})
                print('step %d, training accuracy %g' % (i, train_accuracy))
            train_step.run(feed_dict={x:batch[0], y_: batch[1], keep_prob: 0.5})

        print('test accuracy %g' % accuracy.eval(feed_dict={x: piRNA.test.images, y_:piRNA.test.labels, keep_prob: 1.0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,default='/tmp/tensorflow/mnist/input_data', help='Directory for storing input data')
    FLAGS, unparsed = parser.parse_known_args()
    tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
