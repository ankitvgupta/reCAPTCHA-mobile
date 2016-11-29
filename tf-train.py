import numpy as np
import tensorflow as tf
#from tensorflow.python.ops import rnn, rnn_cell
from sklearn.model_selection import train_test_split
from util import minibatcher, RNN

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

np.save("X_train", X_train)
np.save("Y_train", Y_train)
np.save("X_test", X_test)
np.save("Y_test", Y_test)


x = tf.placeholder("float", [None, n_steps, n_input])
y = tf.placeholder("float", [None, n_classes])
keep_prob = tf.placeholder(tf.float32)
# Define weights
weights = {
    'hidden': tf.Variable(tf.random_normal([n_hidden, n_hidden])),
    'out': tf.Variable(tf.random_normal([n_hidden, n_classes]))
}
biases = {
    'hidden': tf.Variable(tf.random_normal([n_hidden])),
    'out': tf.Variable(tf.random_normal([n_classes]))
}


### Define the various graphs: notably cost, optimizer, and accuracy
pred = RNN(x, weights, biases, n_input, n_steps, n_hidden, keep_prob)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

# # Evaluate model
correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))


sess = tf.Session()


sess.run(tf.initialize_all_variables())

for (rep, (batch_x, batch_y)) in enumerate(minibatcher(X_train,Y_train,10, 20)):
    sess.run(optimizer, feed_dict={x: batch_x, y: batch_y, keep_prob: dropout_keep_prob})
    if rep % 5 == 0:
        # Calculate batch accuracy
        acc = sess.run(accuracy, feed_dict={x: batch_x, y: batch_y, keep_prob: 1.0})
        test_acc = sess.run(accuracy, feed_dict={x: X_test, y: Y_test, keep_prob: 1.0})
        # Calculate batch loss
        loss = sess.run(cost, feed_dict={x: batch_x, y: batch_y, keep_prob: dropout_keep_prob})
        print "Batch " + str(rep) + ", Minibatch Loss= " +               "{:.6f}".format(loss) + ", Training Accuracy= " +               "{:.5f}".format(acc) + ", Test Accuracy= " + "{:.5f}".format(test_acc)
final_test_acc = sess.run(accuracy, feed_dict={x: X_test, y: Y_test, keep_prob: 1.0})
print "Final Test accuracy = " + "{:.5f}".format(final_test_acc)

# In[18]:

saver = tf.train.Saver()


# In[19]:

saver.save(sess, "model.ckpt")


# In[21]:

sess.run(accuracy, feed_dict={x: X_test, y: Y_test, keep_prob: 1.0})


# In[ ]:



