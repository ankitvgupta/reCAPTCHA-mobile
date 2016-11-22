from flask import Flask, render_template, request, redirect, url_for
import smtplib
import json
from email.mime.text import MIMEText

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('captcha.html')

@app.route('/record', methods=['POST'])
def record():
    data = json.loads(request.form['motionData'])

    msg = ""
    for e in data:
        msg += "x: %s, " % (str(e['x']))
        msg += "y: %s, " % (str(e['y']))
        msg += "z: %s, " % (str(e['z']))
        msg += "alpha: %s, " % (str(e['alpha']))
        msg += "beta: %s, " % (str(e['beta']))
        msg += "gamma: %s\n" % (str(e['gamma']))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    with open('password.txt', 'r') as f:
        password = f.read()

    server.login('cs263captcha@gmail.com', password)
    server.sendmail('cs263captcha@gmail.com', 'cs263captcha@gmail.com', MIMEText(msg).as_string())
    server.close()

    return json.dumps("OK")

if __name__ == '__main__':
    app.run(debug=True)
