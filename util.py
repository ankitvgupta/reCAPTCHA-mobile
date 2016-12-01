import tensorflow as tf
from tensorflow.python.ops import rnn, rnn_cell
import numpy as np

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

# time_steps should be an array of size num_steps x num_features
def hash_sequence(time_steps, num_bins=100):

	min_possible = np.array([ -15,   -15,  -50, -400, -400, -250])
	max_possible = np.array([20, 30, 5, 400, 500, 300])
	bin_sizes = (max_possible-min_possible)/np.float(num_bins)
	summed = np.mean(time_steps, axis=0)
	# Keep everything within the above bounds
	for i, v in enumerate(summed):
		if v < min_possible[i]:
			summed[i] = min_possible[i]
		elif v > max_possible[i]:
			summed[i] = max_possible[i]
	# determine the bins
	binned = np.round((summed - min_possible)/bin_sizes)
	x = str(binned)
	return hash(x)
