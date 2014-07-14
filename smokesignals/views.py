import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse, feedparser
from collections import deque
from flask import Flask, request, g, render_template, redirect, session
from smokesignals import app
from smokesignals.models.user import User
from smokesignals.lib.database import Database
import smokesignals.lib.tentlib as tentlib

Flask.secret_key = "ITSASECRETDONTTELLANYONE"

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

@app.route('/preferences', methods=['GET'])
def get_preferences():
    user = User.where("entity=?", (session['entity'],), one=True) 
    return render_template("preferences.html", prefs=user.get_preferences())

@app.route('/preferences', methods=['POST'])
def post_preferences():
    user = User.where("entity=?", (session['entity'],), one=True) 
    newprefs, msg = parse_prefs_form(request.form)
    if msg: return msg
    oldprefs = user.get_preferences()
    newprefs['version'] = oldprefs.get("version", "")
    newprefs['recent_items_cache'] = oldprefs['recent_items_cache']
    user.preferences = newprefs
    user.save_preferences()

    return "Success!"

@app.route('/register', methods=['GET'])
def get_register():
    """ Register a new user. """
    return render_template("register.html")

@app.route('/register', methods=['POST'])
def start_register():
    """ Go through the Tent auth process. """
    entity = request.form['entity'][0:1024].strip()
    session['entity'] = entity

    # Discover entity
    try: session['info'] = tentlib.discover(entity)
    except: return "An error occured while connecting to your entity (discovery failure)."

    # Check that entity is unique
    if User.where("entity=?", (entity,)):
        return "Error: This entity is already registered."

    # Create App Post
    (app_id, app_hawk_key, app_hawk_id) = tentlib.create_ss_app_post(entity)

    # Save our new user
    user = User().create(entity, app_id, app_hawk_key, app_hawk_id)

    # Start OAuth
    session['oauth_redirect'] = "/preferences"

@app.route('/sign_in', methods=['GET'])
def start_sign_in():
    return render_template("signin.html")

@app.route('/sign_in', methods=['POST'])
def finish_sign_in():
    session['entity'] = request.form['entity'][0:1024].strip()
    if not User.where("entity=?", (session['entity'],)):
        return redirect('/register')
    session['oauth_redirect'] = "/preferences"
    return start_oauth('/preferences')
    
def start_oauth(redirect_uri):
    session['oauth_redirect'] = redirect_uri
    if 'entity' not in session:
        return "error: entity not set"
    if 'info' not in session:
        session['info'] = tentlib.discover(session['entity'])

    user = User.where("entity=?", args=(session['entity'],), one=True)

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
        return "Error: Authorization failed. Please try again.\nStates did not match up."

    user = User.where("entity=?", (session['entity'],), one=True)

    token_url = session['info']['post']['content']['servers'][0]['urls']['oauth_token']
    payload = {"code": code, "token_type": "https://tent.io/oauth/hawk-token"}
    req = tentlib.form_oauth_request(token_url, payload, user.app_id, user.app_hawk_key, user.app_hawk_id)
    print(req.headers)

    try:
        res = json.load(urllib2.urlopen(req))
    except urllib2.HTTPError, err:
        print(err.read())
        return "Error: Authorization failed. Please try again."

    user.hawk_key = res['hawk_key']
    user.hawk_id = res['access_token']
    user.save()

    return redirect(session['oauth_redirect'])

@app.route('/unregister', methods=['GET'])
def get_unregister():
    return render_template("unregister.html")

@app.route('/unregister', methods=['POST'])
def start_unregister():
    session['entity'] = request.form['entity'][0:1024].strip()
    return start_oauth("/finish_unregister")

@app.route('/finish_unregister')
def finish_unregister():
    user = User.where("entity=?", (session['entity'],), one=True)
    user.delete()

    return "Successfully deleted %s" % (user.entity)

def parse_prefs_form(form):
    """Takes a form object from a POST to /preferences and returns a proper preferences object as a dict.
       Returns a dict of preferences and an error message or None."""
    if form['source_protocol'] not in ["tent", "rss"]:
        return {}, "Invalid source protocol %s." % (form['source_protocol'])
    if form['post_type'] not in ["status", "essay"]:
        return {}, "Invalid post type." % (form['post_type'])
    try: 
        rss = feedparser.parse("rss_url")
    except: 
        return "Error: Smoke Signals could not parse the RSS feed."

    # Add all items in the feed to recent_items_cache, so they don't all get
    # posted the first time the feed is processed.
    #initial_items = deque([], Feed.recent_items_cache_size)
    #for entry in rss['entries']:
    #    initial_items.appendleft(Feed.hashable_entry(entry))
    #feed.recent_items_cache = initial_items
    #feed.save()

    return  {
        "source_protocol": form["source_protocol"],
        "post_type": form["post_type"],
        "rss_url": form["rss_url"],
    }, None
            
