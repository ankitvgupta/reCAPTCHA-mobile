# reCAPTCHA-mobile

reCAPTCHA-mobile is an implementation of reCAPTCHA agent verification for mobile browsers. It works by using accelerometer data from mobile phones which are accessible through Javascript.

## File and Directory Structure

- [tf-train.py](tf-train.py): This is the central training file. This file loads a particular dataset from disk, trains a configured recurrent neural network model with it, and saves the model along with the associated training and testing files to disk.
- [util.py](util.py): Contains various utility functions used in the testing and training process.
- [loaded.ipynb](loaded.ipynb): This is an iPython Notebook that we used to test the trained models with a test set.
- [ckpt/*](ckpt): Contains the trained models
- [npy/*](npy): Contains the training and test files that are emitted for a particular model
