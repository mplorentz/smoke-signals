import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse, feedparser
from collections import deque
from functools import wraps
from flask import Flask, request, g, render_template, redirect, session, flash
from smokesignals import app
from smokesignals.models.user import User
from smokesignals.models.prefs import Prefs
from smokesignals.lib.database import Database
import smokesignals.lib.tentlib as tentlib

Flask.secret_key = "ITSASECRETDONTTELLANYONE"

def auth(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if 'authenticated' not in session:
            flash("You need to log in first.", "error")
            return redirect("sign_in")
        else: 
            return f(*args, **kwargs)
    return decorator

@app.route('/')
def home():
    """ Main landing page. """
    return render_template("home.html")

@app.route('/feed')
def feed():
    """ View a feed, so we know parsing is working. """
    url = request.args.get('url', '')
    if not url:
        return "no url"

    data = feedparser.parse(url)
    return str(data)

@app.route('/sign_in', methods=['GET'])
def start_sign_in():
    return render_template("sign_in.html")

@app.route('/sign_in', methods=['POST'])
def finish_sign_in():
    entity = request.form['entity'][0:1024].strip()
    if not User.where("entity=?", (entity,)):
        try: 
            session['info'] = tentlib.discover(entity)
        except: 
            flash("An error occured while connecting to your entity (discovery failure).", 'error')
            return render_template('sign_in.html')
        (app_id, app_hawk_key, app_hawk_id) = tentlib.create_ss_app_post(entity)
        user = User().create(entity, app_id, app_hawk_key, app_hawk_id)
        flash('You have registered successfully')

    session['entity'] = entity
    return start_oauth('/preferences')

@app.route('/preferences', methods=['GET'])
@auth
def get_preferences():
    user = User.where("entity=?", (session['entity'],), one=True) 
    return render_template("preferences.html", prefs=user.get_preferences())

@app.route('/preferences', methods=['POST'])
@auth
def post_preferences():
    prefs, msg = Prefs.expand(session['entity'], request.form)
    if msg: 
        flash(msg, 'error')
        return redirect('preferences')
    prefs.save()
    flash("Saved!")
    return redirect('preferences')

@app.route('/sign_out')
@auth
def sign_out():
    session.clear()
    flash('You have been successfully logged out.')
    return redirect('/')
    
def start_oauth(redirect_uri):
    session['oauth_redirect'] = redirect_uri
    if 'entity' not in session:
        flash("Internal Error: Entity not set", 'error')
        return redirect("/sign_in")
    if 'info' not in session:
        session['info'] = tentlib.discover(session['entity'])

    user = User.where("entity=?", (session['entity'],), one=True)

    oauth_url = session['info']['post']['content']['servers'][0]['urls']['oauth_auth']
    state = tentlib.randomword(10)
    session['state'] = state

    return redirect("%s?client_id=%s&state=%s" % (oauth_url, user.app_id, state))

@app.route('/finish_auth')
def finish_auth():
    code = request.args.get('code')
    state = request.args.get('state')

    # verify the state
    if state != session['state']:
        flash("Error: Authorization failed. Please try again.\nStates did not match up.", "error")
        return redirect("/sign_in")

    user = User.where("entity=?", (session['entity'],), one=True)

    token_url = session['info']['post']['content']['servers'][0]['urls']['oauth_token']
    payload = {"code": code, "token_type": "https://tent.io/oauth/hawk-token"}
    req = tentlib.form_oauth_request(token_url, payload, user.app_id, user.app_hawk_key, user.app_hawk_id)
    print(req.headers)

    try:
        res = json.load(urllib2.urlopen(req))
    except urllib2.HTTPError, err:
        print(err.read())
        flash("Error: Authorization failed. Please try again.", "error")
        return redirect("/sign_in")

    user.hawk_key = res['hawk_key']
    user.hawk_id = res['access_token']
    user.save()
    session['authenticated'] = True

    return redirect(session['oauth_redirect'])

@app.route('/unregister', methods=['GET'])
@auth
def start_unregister():
    return render_template("unregister.html")

@app.route('/unregister', methods=['POST'])
@auth
def finish_unregister():
    user = User.where("entity=?", (session['entity'],), one=True)
    user.delete()
    session.clear()
    flash("Successfully deleted %s" % (user.entity))
    return redirect("/")
