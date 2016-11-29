import tensorflow as tf
from tensorflow.python.ops import rnn, rnn_cell

def minibatcher(data_x, data_y, batch_size, num_repeats):
    assert(data_x.shape[0])
    data_size = data_x.shape[0]
    for _ in range(num_repeats):
        start = 0
        while start < data_size:
            yield data_x[start:start + batch_size], data_y[start:start + batch_size]
            start += batch_size

def RNN(x, weights, biases, n_input, n_steps, n_hidden, keep_prob):

    # Prepare data shape to match `rnn` function requirements
    # Current data input shape: (batch_size, n_steps, n_input)
    # Required shape: 'n_steps' tensors list of shape (batch_size, n_input)
    
    # Permuting batch_size and n_steps
    x = tf.transpose(x, [1, 0, 2])
    # Reshaping to (n_steps*batch_size, n_input)
    x = tf.reshape(x, [-1, n_input])
    # Split to get a list of 'n_steps' tensors of shape (batch_size, n_input)
    x = tf.split(0, n_steps, x)

    # Define a lstm cell with tensorflow
    lstm_cell = rnn_cell.BasicLSTMCell(n_hidden, forget_bias=1.0)

    # Get lstm cell output
    outputs, states = rnn.rnn(lstm_cell, x, dtype=tf.float32)

    hidden_layer = tf.nn.relu(tf.matmul(outputs[-1], weights['hidden']) + biases['hidden'])
    hidden_layer = tf.nn.dropout(hidden_layer, keep_prob)
    return tf.matmul(hidden_layer, weights['out']) + biases['out']
    
    
    # Linear activation, using rnn inner loop last output
    # return tf.matmul(outputs[-1], weights['out']) + biases['out']

