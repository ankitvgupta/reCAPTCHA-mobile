import numpy as np
import tensorflow as tf
#from tensorflow.python.ops import rnn, rnn_cell
from sklearn.model_selection import train_test_split
from util import minibatcher, RNN, hash_sequence

classes = ["walking", "sitting", "table", "stairs", "car"]

n_hidden = 100 # Size of the LSTM hidden layer
batch_size = 8 # Number of data points in a batch
learning_rate = 0.01 # Learning rate of the optimizer
dropout_keep_prob = .8


clean_data = np.load("gmail/clean_data.npy")
data_labels = np.load("gmail/labels.npy")

# Update the dataset to only be the labeled data (the ones that aren't 0)
labeled = data_labels != 0
input_motion_data = clean_data[labeled]
output_motion_data = data_labels[labeled] - 1 # Need to decrement by 1 since we removed all the 0s
n_samples = input_motion_data.shape[0]
n_steps = input_motion_data.shape[1]
n_input = input_motion_data.shape[2]
n_classes = np.max(output_motion_data) + 1

output_classes = np.zeros((n_samples, n_classes))
for i in range(n_samples):
    output_classes[i, output_motion_data[i]] = 1


X_train_unfiltered, X_test, Y_train_unfiltered, Y_test = train_test_split(input_motion_data, output_classes, test_size=.2)


counts_per_class = np.bincount(np.argmax(Y_train_unfiltered, axis=1))
smallest_class_size = min(counts_per_class)


X_train = np.zeros((smallest_class_size*n_classes, X_train_unfiltered.shape[1], X_train_unfiltered.shape[2]))
Y_train = np.zeros((smallest_class_size*n_classes, Y_train_unfiltered.shape[1]))

num_in_class = np.zeros(n_classes)
loc = 0
for x, y in zip(X_train_unfiltered, Y_train_unfiltered):
    class_of_sample = np.argmax(y)
    if num_in_class[class_of_sample] >= smallest_class_size:
        continue
    X_train[loc] = x
    Y_train[loc] = y
    num_in_class[class_of_sample] += 1
    loc += 1


mins = np.zeros((input_motion_data.shape[0], input_motion_data.shape[2]))
maxs = np.zeros((input_motion_data.shape[0], input_motion_data.shape[2]))
for i in range(input_motion_data.shape[0]):
    mins[i] = np.min(input_motion_data[i], axis=0)
    maxs[i] = np.max(input_motion_data[i], axis=0)

#print(np.min(mins, axis=0))
#print(np.max(maxs, axis=0))

seq = X_train[0]
noise_to_add = 0.0
hash_val = hash_sequence(seq)
new_hash = hash_val
print(hash_val)
while new_hash == hash_val:
    noise = np.random.normal(noise_to_add, .001, seq.shape)
    new_seq = seq + noise
    new_hash = hash_sequence(new_seq)
    noise_to_add += .001
print(noise_to_add)





