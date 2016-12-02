# reCAPTCHA-mobile

reCAPTCHA-mobile is an implementation of reCAPTCHA agent verification for mobile browsers. It works by using accelerometer data from mobile phones which are accessible through Javascript.

## Server Code
We wrote two servers in implementing this project. 
- [data-capture/*](data-capture): Contains the code for the web-server we wrote to get experimental data from our phones. We hosted two pages from this server on heroku, which are accessibly at (1) cs263.herokuapp.com and (2) cs263.herokuapp.com/experiment. 
  1. The first of these was used to collect data from users. When users click the button in the page, we get 5 seconds of motion data from their phone's accelerometer.
  2. The second of these was used for us to collect annotated data. We type a text label, and then can repeatedly send samples from our phone while we perform an activity that corresponds to that label, such as walking, sitting, being in a car, etc.
- [captcha-server/*](captcha-server): Contains the code for the web-server we wrote for the central CAPTCHA server described in detail in section 4 of the paper. The [captcha-server/app.py](app.py) file contains all of the server-side code. The [captcha-server/templates/register.html](register.html) page contains the client side code for displaying client key registrations to users and allowing users to manage keys.

## Data Collection and Storage
To actually collect the data, we used deployed the server in [data-capture/*](data-capture) on heroku. The server sent data to cs263captcha@gmail.com. Then, we wrote a quick script, which you can find in [gmail/*](gmail) to download the data from that gmail account, clean it up, load it into an appropriate format, and save it to a file.

## Model Training 

- [tf-train.py](tf-train.py): This is the central training file. This file loads a particular dataset from disk, trains a configured recurrent neural network model with it, and saves the model along with the associated training and testing files to disk.
- [util.py](util.py): Contains various utility functions used in the testing and training process.
- [loaded.ipynb](loaded.ipynb): This is an iPython Notebook that we used to test the trained models with a test set.
- [ckpt/*](ckpt): Contains the trained models
- [npy/*](npy): Contains the training and test files that are emitted for a particular model
