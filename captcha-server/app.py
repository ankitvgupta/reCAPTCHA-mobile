from flask import Flask, render_template, request, redirect, url_for, session
from flask_oauth import OAuth

from Crypto.Random import random
import json
import pickledb
from urllib2 import Request, urlopen, URLError

KEYLENGTH = 40
MAXDOMAINS = 10

with open('secrets.json') as secrets:
    data = json.loads(secrets.read())
    GOOGLE_CLIENT_ID = data['google_client_id']
    GOOGLE_CLIENT_SECRET = data['google_client_secret']
    SECRET_KEY = data['flask_secret']

REDIRECT_URI = '/oauth2callback'

app = Flask(__name__)
app.secret_key = SECRET_KEY

oauth = OAuth()
google = oauth.remote_app('google',
                          base_url='https://www.google.com/accounts/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
                                                'response_type': 'code'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)

@app.route('/register')
def register():
    login_token = session.get('login_token')
    print login_token
    if login_token is None:
        return redirect(url_for('login'))

    headers = {'Authorization': 'OAuth ' + login_token[0]}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo', None, headers)

    try:
        res = urlopen(req)
    except URLError, e:
        print e
        if e.code == 401:
            # Bad token
            session.pop('access_token', None)
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login')
def login():
    callback_url = url_for('authorized', _external=True)
    return google.authorize(callback=callback_url)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(oauth_resp):
    login_token = oauth_resp['access_token']
    session['login_token'] = login_token, ''
    return redirect(url_for('register'))

@google.tokengetter
def get_login_token():
    return session.get('login_token')

@app.route('/new_registration', methods=['POST'])
def new_registration():
    def randomString(length):
        import string
        charset = string.ascii_letters + string.digits + '-_!'
        return ''.join(random.choice(charset) for _ in range(length))

    def newKeyPair(db):
        while True:
            siteID = randomString(KEYLENGTH)
            if db.get(siteID) == None:
                break

        secret = randomString(KEYLENGTH)
        return siteID, secret

    domains = request.form['domains']
    if len(domains) == 0:
        return "Must specify at least one domain", 400

    domains = [s.strip() for s in domains.split('\n')]
    if len(domains) > MAXDOMAINS:
        return "Specified too many domains", 400

    db = pickledb.load('sites.db', False)
    pair = newKeyPair(db)

    db.set(pair[0], (pair[1], domains))
    db.dump()

    response = json.dumps({'siteID': pair[0], 'secret': pair[1]})

    return response

if __name__ == '__main__':
    app.run(debug=True)
