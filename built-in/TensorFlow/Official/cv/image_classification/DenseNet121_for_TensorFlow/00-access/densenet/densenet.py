import tensorflow as tf
from tensorflow.contrib.layers import batch_norm, flatten
from tensorflow.contrib.framework import arg_scope
import numpy as np

class_num = 1000
nb_blocks = 4
nb_blocks_layers = (6, 12, 24, 16)
bn_size = 4
growth_rate = 32
init_layers = 64


'''
denseNet：121，169，201，264
return _densenet('densenet121', 32, (6, 12, 24, 16), 64, pretrained, progress,
                     **kwargs)
return _densenet('densenet161', 48, (6, 12, 36, 24), 96, pretrained, progress,
                     **kwargs)
return _densenet('densenet169', 32, (6, 12, 32, 32), 64, pretrained, progress,
                     **kwargs)
return _densenet('densenet201', 32, (6, 12, 48, 32), 64, pretrained, progress,
                     **kwargs)                     
'''



def conv_layer(input, filter, kernel, stride=1, layer_name="conv"):
    with tf.name_scope(layer_name):
        network = tf.layers.conv2d(inputs=input, filters=filter, kernel_size=kernel, strides=stride, padding='SAME', use_bias=False, kernel_initializer=tf.initializers.variance_scaling(scale=5.0, mode='fan_out')) # scale=5.0, mode='fan_out'
        return network

def Global_Average_Pooling(x, stride=1):
    
    width = np.shape(x)[1]
    height = np.shape(x)[2]
    pool_size = [width, height]
    return tf.layers.average_pooling2d(inputs=x, pool_size=pool_size, strides=stride) # The stride value does not matter
    #It is global average pooling without tflearn
    

    #return global_avg_pool(x, name='Global_avg_pooling')
    # But maybe you need to install h5py and curses or not


def Batch_Normalization(x, training, scope):
    with arg_scope([batch_norm],
                   scope=scope,
                   updates_collections=None,
                   decay=0.9,
                   center=True,
                   scale=True,
                   zero_debias_moving_mean=True) :
        training = tf.cast(training, tf.bool)
        return tf.cond(training,
                       lambda : batch_norm(inputs=x, is_training=training, reuse=None),
                       lambda : batch_norm(inputs=x, is_training=training, reuse=True))

def Drop_out(x, rate, training) :
    return tf.layers.dropout(inputs=x, rate=rate, training=training)

def Relu(x):
    return tf.nn.relu(x)

def Average_pooling(x, pool_size=[2,2], stride=2, padding='VALID'):
    return tf.layers.average_pooling2d(inputs=x, pool_size=pool_size, strides=stride, padding=padding)


def Max_Pooling(x, pool_size=[3,3], stride=2, padding='VALID'):
    return tf.layers.max_pooling2d(inputs=x, pool_size=pool_size, strides=stride, padding=padding)

def Concatenation(layers):
    return tf.concat(layers, axis=3)

def Linear(x):
    return tf.layers.dense(inputs=x, units=class_num, name='linear')


def bottleneck_layer(x, is_training, scope):
    # print(x)
    with tf.name_scope(scope):
        x = Batch_Normalization(x, training=is_training, scope=scope+'_batch1')
        x = Relu(x)
        x = conv_layer(x, filter= growth_rate*bn_size, kernel=[1,1], layer_name=scope+'_conv1')
        #x = Drop_out(x, rate=dropout_rate, training=is_training)
        #x = Drop_out(x, rate=dropout_rate, training=is_training)

        x = Batch_Normalization(x, training=is_training, scope=scope+'_batch2')
        x = Relu(x)
        x = conv_layer(x, filter= growth_rate, kernel=[3,3], layer_name=scope+'_conv2')
        #x = Drop_out(x, rate=dropout_rate, training=self.training)

        # print(x)

        return x

def transition_layer(x, is_training, scope):
    with tf.name_scope(scope):
        x = Batch_Normalization(x, training=is_training, scope=scope+'_batch1')
        x = Relu(x)
        # x = conv_layer(x, filter=self.filters, kernel=[1,1], layer_name=scope+'_conv1')
        
        # https://github.com/taki0112/Densenet-Tensorflow/issues/10
        
        in_channel = int(x.shape[-1])
        x = conv_layer(x, filter=in_channel*0.5, kernel=[1,1], layer_name=scope+'_conv1')
        #x = Drop_out(x, rate=dropout_rate, training=self.training)
        x = Average_pooling(x, pool_size=[2,2], stride=2)

        return x

def dense_block(input_x, nb_layers, is_training, layer_name):
    with tf.name_scope(layer_name):
        layers_concat = list()
        layers_concat.append(input_x)

        x = bottleneck_layer(input_x, is_training, scope=layer_name + '_bottleN_' + str(0))

        layers_concat.append(x)

        for i in range(nb_layers - 1):
            x = Concatenation(layers_concat)
            x = bottleneck_layer(x, is_training, scope=layer_name + '_bottleN_' + str(i + 1))
            layers_concat.append(x)

        x = Concatenation(layers_concat)

        return x

def Dense_net(input_x, is_training):
    x = conv_layer(input_x, filter=init_layers , kernel=[7,7], stride=2, layer_name='conv0')
    x = Max_Pooling(x, pool_size=[3,3], stride=2)

    for i in range(nb_blocks-1) :
        # 6 -> 12 -> 48
        x = dense_block(input_x=x, nb_layers=nb_blocks_layers[i], is_training=is_training, layer_name='dense_'+str(i))
        x = transition_layer(x, is_training, scope='trans_'+str(i))

    """
    x = self.dense_block(input_x=x, nb_layers=6, layer_name='dense_1')
    x = self.transition_layer(x, scope='trans_1')
    x = self.dense_block(input_x=x, nb_layers=12, layer_name='dense_2')
    x = self.transition_layer(x, scope='trans_2')
    x = self.dense_block(input_x=x, nb_layers=48, layer_name='dense_3')
    x = self.transition_layer(x, scope='trans_3')
    """

    x = dense_block(input_x=x, nb_layers=nb_blocks_layers[nb_blocks-1], is_training=is_training, layer_name='dense_final')

    # 100 Layer
    x = Batch_Normalization(x, training=is_training, scope='linear_batch')
    x = Relu(x)
    x = Global_Average_Pooling(x)
    x = flatten(x)
    x = Linear(x)

    # x = tf.reshape(x, [-1, 10])
    return x
