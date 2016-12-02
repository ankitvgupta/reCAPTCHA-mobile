from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_oauth import OAuth

from Crypto.Random import random
import numpy as np
import tensorflow as tf
from tensorflow.python.ops import rnn, rnn_cell
import datetime, dateutil.parser, json, pickledb, sys, re

sys.path.append("..")
import util

KEYLENGTH = 40
TOKENLENGTH = 420
MAXPERUSER = 5
TOKEN_LIFE_SECONDS = 60

with open('secrets.json') as secrets:
    data = json.loads(secrets.read())
    GOOGLE_CLIENT_ID = data['google_client_id']
    GOOGLE_CLIENT_SECRET = data['google_client_secret']
    SECRET_KEY = data['flask_secret']

REDIRECT_URI = '/oauth2callback'

SITES_DB = 'sites.db'
USERS_DB = 'users.db'
TOKENS_DB = 'tokens.db'

hashes = []

app = Flask(__name__)
app.secret_key = SECRET_KEY

oauth = OAuth()
google = oauth.remote_app('google',
                          base_url='https://www.googleapis.com/oauth2/v1/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
                                                'response_type': 'code'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)

n_hidden = 100 # Size of the LSTM hidden layer
batch_size = 8 # Number of data points in a batch
learning_rate = 0.01 # Learning rate of the optimizer
dropout_keep_prob = .8

model_name = "../mix_model"
model_fake_data = "../mix.npy"

clean_data = np.load("../gmail/clean_data.npy")
data_labels = np.load("../gmail/labels.npy")
fake_data = np.load(model_fake_data)

n_human = clean_data.shape[0]
n_robot = fake_data.shape[0]
input_motion_data = np.append(clean_data, fake_data, axis=0)
output_motion_data = np.append(np.ones(n_human), np.zeros(n_robot)).astype(int)
n_samples = input_motion_data.shape[0]
n_steps = input_motion_data.shape[1]
n_input = input_motion_data.shape[2]
n_classes = np.max(output_motion_data) + 1

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

pred = util.RNN(x, weights, biases, n_input, n_steps, n_hidden, keep_prob)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

# Evaluate model
correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

# Later, launch the model, use the saver to restore variables from disk, and
# do some work with the model.
sess = tf.Session()
# Restore variables from disk.
saver.restore(sess, model_name + ".ckpt")


@app.route('/error')
def error():
    return "Something went wrong :("

@app.route('/login')
def login():
    callback_url = url_for('authorized', _external=True)
    return google.authorize(callback=callback_url)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(oauth_resp):
    if oauth_resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )

    login_token = oauth_resp['access_token']
    session['login_token'] = login_token, ''

    resp = google.get('userinfo')
    if resp.status != 200:
        session.pop('login_token', None)
        return redirect(url_for('error'))
    else: 
        session['email'] = resp.data['email']
        return redirect(url_for('register'))

@google.tokengetter
def get_login_token():
    return session.get('login_token')


@app.route('/register')
def register():
    if 'login_token' not in session or 'email' not in session:
        return redirect(url_for('login'))

    db = pickledb.load(USERS_DB, False)
    registrations = db.get(session['email'])

    return render_template('register.html', 
                            session=session,
                            registrations=registrations,
                            maxperuser=MAXPERUSER)

@app.route('/delete', methods=['POST'])
def delete_registration():
    if 'login_token' not in session or 'email' not in session:
        return redirect(url_for('login'))

    siteID = request.form['siteID']

    user_db = pickledb.load(USERS_DB, False)
    site_db = pickledb.load(SITES_DB, False)

    regs = user_db.get(session['email'])

    if regs is None:
        return "User has no registered keys", 403

    found = False
    for i, r in enumerate(regs):
        if r[1] == siteID:
            del regs[i]
            found = True
            break

    if not found:
        return "SiteID does not belong to user", 403

    site = site_db.get(siteID)
    if site is None:
        return "SiteID not found", 403

    user_db.set(session['email'], regs)
    site_db.rem(siteID)

    user_db.dump()
    site_db.dump()

    return "OK"


def randomString(length):
    import string
    charset = string.ascii_letters + string.digits + '-_!'
    return ''.join(random.choice(charset) for _ in range(length))

@app.route('/new_registration', methods=['POST'])
def new_registration():
    if 'login_token' not in session or 'email' not in session:
        return redirect(url_for('login'))

    def newKeyPair(db):
        while True:
            siteID = randomString(KEYLENGTH)
            if db.get(siteID) == None:
                break

        secret = randomString(KEYLENGTH)
        return siteID, secret

    label = request.form['label']
    if len(label) == 0:
        return "Must specify a label", 400

    email = session['email']
    user_db = pickledb.load(USERS_DB, False)
    site_db = pickledb.load(SITES_DB, False)
    token_db = pickledb.load(TOKENS_DB, False)

    registrations = user_db.get(email)
    if (registrations and len(registrations) >= MAXPERUSER):
        return "Signed up for max keys", 403

    pair = newKeyPair(site_db)

    site_db.set(pair[0], (str(label), pair[1]))
    site_db.dump()

    if registrations == None:
        user_db.set(email, [(str(label), pair[0], pair[1])])
    else:
         user_db.set(email, registrations + [(str(label), pair[0], pair[1])])
    user_db.dump()

    token_db.set(pair[0], [])
    token_db.dump()

    response = json.dumps({'siteID': pair[0], 'secret': pair[1]})

    return response

def extract_data(line):
    m = re.match("x: (.*), y: (.*), z: (.*), alpha: (.*), beta: (.*), gamma: (.*)", line)
    strings = [m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)]
    for string in strings:
        if string == "None":
            return []
        
    return map(float, strings)

@app.route('/token', methods=['POST'])
def token():
    siteID = request.form['siteID']
    data = request.form['data']

    token_db = pickledb.load(TOKENS_DB, False)
    token_list = token_db.get(siteID) 

    if token_list is None:
        return "Invalid siteID", 400

    def validate_data(data):
        h = util.hash_sequence(data)
        if h in hashes:
            return (False, h)

        data = np.array([data])
        klass = np.argmax(sess.run(pred, feed_dict={x: data, keep_prob: 1.0}))
        if klass == 0:
            return (False, h) # Robot
        else:
            return (True, h) # Human

    # try:
    token = randomString(TOKENLENGTH)

    lines = data.splitlines()
    data = []
    for line in lines:
        data.append(extract_data(line))

    if len(data) < 260:
        return "Invalid data", 400
    else:
        data = data[:260]

    valid, h = validate_data(data)
    if valid:
        hashes.append(h)
        time = datetime.datetime.now().isoformat()
        token_list.append((token,time))

        token_db.set(siteID, token_list)
        token_db.dump()
        return token, 200
    else:
        return token, 200
# except:
    return "Invalid data", 400

@app.route('/verify', methods=['POST'])
def verify():
    siteID = request.form['siteID']
    secret = request.form['secret']
    token = request.form['token']

    site_db = pickledb.load(SITES_DB, False)
    site = site_db.get(siteID)

    if site is None:
        return "invalid siteID", 400
    if site[1] != secret:
        return "invalid secret", 403

    token_db = pickledb.load(TOKENS_DB, False)
    tokens = token_db.get(siteID)
    for i, t in enumerate(tokens):
        if t[0] == token:
            del tokens[i]
            token_db.set(siteID, tokens)
            token_db.dump()

            time = dateutil.parser.parse(t[1])
            if (datetime.datetime.now() - time).total_seconds() < TOKEN_LIFE_SECONDS:
                return "OK", 200
            else:
                return "Expired token", 403

    return "Invalid token", 403

if __name__ == '__main__':
    app.run(debug=True)
