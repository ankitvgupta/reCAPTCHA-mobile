from flask import Flask, render_template, request, redirect, url_for
from Crypto.Random import random
import json, string
import pickledb

KEYLENGTH = 40
MAXDOMAINS = 10

app = Flask(__name__)

def randomString(length):
    charset = string.ascii_letters + string.digits + '-_!'
    return ''.join(random.choice(charset) for _ in range(length))

def newKeyPair(db):
    while True:
        siteID = randomString(KEYLENGTH)
        if db.get(siteID) == None:
            break

    secret = randomString(KEYLENGTH)
    return siteID, secret

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/new_registration', methods=['POST'])
def new_registration():
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
