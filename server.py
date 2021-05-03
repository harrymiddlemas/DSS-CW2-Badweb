import datetime
import os
import random
import sqlite3
import time
from datetime import timedelta
from functools import wraps
import numpy as np
import cv2
import hash

import flask
from PIL import ImageFont, ImageDraw, Image
from flask import Flask, g, render_template, redirect, request, session, url_for

import encoder

app = Flask(__name__)

context = ('local.crt', 'local.key')  # certificate and key files

app.secret_key = 't6w9z$C&F)J@NcRf'
app.permanent_session_lifetime = timedelta(minutes=60)
app.SESSION_COOKIE_HTTPONLY = True
app.SESSION_COOKIE_SAMESITE = 'Strict'

DATABASE = 'database.sqlite'


# Track the times of recent requests from an IP
ipRequests = {}

# Maximum number of requests per second per IP
maxRequestRate = 10;

# Enforce rate limiting on each request, blocking if IP exceeds max requests per second.
@app.before_request
def new_rate_limit():
    ip = request.remote_addr
    updated = set()
    if ip in ipRequests:
        requests = ipRequests[ip]
        # Iterate times of IPs recent requests
        for time in requests:
            # If a request was within last second, add to updated set
            if (datetime.datetime.now() - time).seconds < 1:
                updated.add(time)
    # Add current requests time
    updated.add(datetime.datetime.now())
    # Update IPs requests set
    ipRequests[ip] = updated
    # If set exceeds max rate, deny access
    if len(updated) > maxRequestRate:
        return redirect(url_for('access_denied'))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    def make_dicts(cursor, row):
        return dict((cursor.description[idx][0], value)
                    for idx, value in enumerate(row))

    db.row_factory = make_dicts

    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def std_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        context = {}
        request.context = context
        if 'userid' in session:
            context['loggedin'] = True
            context['username'] = session['username']
        else:
            context['loggedin'] = False
        return f(*args, **kwargs)

    return wrapper


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
@std_context
def index():
    posts = query_db(
        'SELECT posts.creator,posts.date,posts.title,posts.content,users.name,users.username,users.USER_PATH_ID FROM '
        'posts JOIN users ON posts.creator=users.userid ORDER BY date DESC LIMIT 10')

    def fix(item):
        item['date'] = datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M')
        item['content'] = '%s...' % (item['content'][:200])
        return item

    context = request.context

    context['posts'] = map(fix, encoder.encode_qry(posts))
    return render_template('index.html', **context)


@app.route("/<uname>/")
@std_context
def users_posts(uname=None):
    cid = query_db('SELECT userid FROM users WHERE username=(?)', (uname,))
    if len(cid) < 1:
        return 'No such user'

    cid = cid[0]['userid']

    if 'userid' in session.keys() and session['userid'] == cid:
        query = 'SELECT date,title,content FROM posts WHERE creator=(?) ORDER BY date DESC'

        context = request.context

        def fix(item):
            item['date'] = datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M')
            return item

        context['posts'] = map(fix, encoder.encode_qry(query_db(query)))
        return render_template('user_posts.html', **context)
    return 'Access Denied'


@app.route("/user_path_id/<user_path_id>/")
@std_context
def users_posts_by_user_path_id(user_path_id=None):
    cid = query_db('SELECT userid FROM users WHERE USER_PATH_ID=%s' % (user_path_id))
    if len(cid) < 1:
        return 'No such user'

    query = 'SELECT date,title,content, USER_PATH_ID FROM POSTS NATURAL JOIN USERS WHERE USER_PATH_ID=%s ORDER BY ' \
            'date DESC' % user_path_id

    context = request.context

    def fix(item):
        item['date'] = datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M')
        return item

    results = query_db(query)
    context['posts'] = map(fix, encoder.encode_qry(results))
    return render_template('user_posts.html', **context)


def generate_captcha_string():
    char_options = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    captcha_string = ''
    for i in range(7):
        captcha_string += char_options[random.randint(1, len(char_options)-1)]
    return captcha_string


def create_captcha_image(captcha_text, filename):
    size = random.randint(10, 16)
    length = random.randint(4, 8)
    image = np.zeros(shape=(size * 2 + 5, length * size, 3), dtype=np.uint8)
    image_pil = Image.fromarray(image + 255)
    draw = ImageDraw.Draw(image_pil)
    font = ImageFont.truetype(font='arial', size=12)
    draw.text((5, 10), captcha_text, font=font,
              fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    draw.line([(random.choice(range(length * size)), random.choice(range((size * 2) + 5))),
               (random.choice(range(length * size)), random.choice(range((size * 2) + 5)))],
              width=1, fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    threshold = random.randint(1, 5) / 100
    img_with_salt = np.array(image_pil)
    for i in range(img_with_salt.shape[0]):
        for j in range(img_with_salt.shape[1]):
            rdn = random.random()
            if rdn < threshold:
                img_with_salt[i][j] = random.randint(0, 123)
            elif rdn > 1 - threshold:
                img_with_salt[i][j] = random.randint(123, 255)
    img_blurred_with_salt = cv2.blur(img_with_salt,
                                     (int(size / random.randint(5, 10)), int(size / random.randint(5, 10))))
    Image.fromarray(img_blurred_with_salt).save(filename)


@app.route("/captcha-check/", methods=['GET', 'POST'])
@std_context
def captcha_check():
    captcha_input = request.form.get('captcha', '')
    context = request.context
    context['filename'] = str(round(time.time())) + '.png'
    if captcha_input != '' and captcha_input.lower() == session['data'].lower():
        ip = flask.request.remote_addr
        session.pop(ip)
        return redirect(url_for('login'))
    for file in os.listdir('static/'):
        if file.endswith('.png'):
            os.remove('static/' + file)
    session['data'] = generate_captcha_string()
    create_captcha_image(session['data'], 'static/' + context['filename'])
    return render_template('captcha.html', **context)


@app.route("/login/", methods=['GET', 'POST'])
@std_context
def login():
    ip = flask.request.remote_addr
    if ip in session.keys():
        session[ip] = session[ip] + 1
    else:
        session[ip] = 1

    if session[ip] > 3:
        return redirect(url_for('captcha_check'))

    username = request.form.get('username', '')
    password = request.form.get('password', '')
    context = request.context

    if len(username) < 1 and len(password) < 1:
        return render_template('login.html', **context)

    query = "SELECT userid FROM users WHERE username=(?)"
    account = query_db(query, (username,))
    user_exists = len(account) > 0

    pass_match = False
    query = "SELECT salt FROM users WHERE username=(?)"
    salt = query_db(query, (username,))
    if len(salt) > 0:
        hashed = hash.hash(password + salt[0]['salt'])
        query = "SELECT userid FROM users WHERE username=(?) AND hash=(?)"
        account2 = query_db(query, (username, hashed))
        pass_match = len(account2) > 0

    if user_exists and pass_match:
        session['userid'] = account[0]['userid']
        session['username'] = username
        session['token'] = str(os.urandom(16))
        session.permanent = True
        return redirect(url_for('index'))
    else:
        # Username or password incorrect
        return redirect(url_for('login_fail', error='Username or password incorrect'))


@app.route("/loginfail/")
@std_context
def login_fail():
    context = request.context
    context['error_msg'] = request.args.get('error', 'Unknown error')
    return render_template('login_fail.html', **context)


@app.route("/logout/")
def logout():
    session.pop('userid', None)
    session.pop('username', None)
    return redirect('/')


@app.route("/post/", methods=['GET', 'POST'])
@std_context
def new_post():
    if 'userid' not in session:
        return redirect(url_for('login'))

    userid = session['userid']
    context = request.context

    if request.method == 'GET':
        session['token'] = str(os.urandom(16))
        return render_template('new_post.html', token=session.get('token'), **context)

    csrf = request.form.get('csrf')

    if csrf == session.get('token'):
        date = datetime.datetime.now().timestamp()
        title = request.form.get('title')
        content = request.form.get('content')
        query = "INSERT INTO posts (creator, date, title, content) VALUES ((?), (?), (?), (?))"
        query_db(query, (userid, date, title, content))
        get_db().commit()

    return redirect('/')


@app.route("/reset/", methods=['GET', 'POST'])
@std_context
def reset():
    context = request.context

    email = request.form.get('email', '')
    if email == '':
        return render_template('reset_request.html')

    context['email'] = encoder.encode(email)
    return render_template('sent_reset.html', **context)


@app.route("/search/")
@std_context
def search_page():
    context = request.context
    search = request.args.get('s', '')

    wildcard = '%' + search + '%'
    print(wildcard)

    query = """SELECT username FROM users WHERE username LIKE (?);"""
    users = query_db(query, (wildcard,))

    context['users'] = encoder.encode_qry(users)
    context['query'] = encoder.encode(search)
    return render_template('search_results.html', **context)


@app.route("/access_denied/")
@std_context
def access_denied():
    return render_template("access_denied.html")


if __name__ == '__main__':
    app.run(ssl_context=('server.crt', 'server.key'))
