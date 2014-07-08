import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse, feedparser, os
from collections import deque
from flask import Flask, request, g, render_template, redirect, session
from smokesignals import app
from smokesignals.models.user import User
from smokesignals.models.feed import Feed
from smokesignals.lib.database import Database
import smokesignals.lib.tentlib as tentlib

Flask.secret_key = os.environ['FLASK_SECRET']

@app.route('/')
def main():
    """ Main landing page. """
    return "smoke signals connect tent and rss!"

@app.route('/feed')
def feed():
    """ View a feed, so we know parsing is working. """
    url = request.args.get('url', '')
    if not url:
        return "no url"

    data = feedparser.parse(url)
    return str(data)

@app.route('/register', methods=['GET'])
def get_register():
    """ Register a new user. """
    return render_template("register.html")

@app.route('/register', methods=['POST'])
def start_register():
    """ Go through the Tent auth process. """
    entity = request.form['entity'][0:1024].strip()
    feed_url = request.form['feed_url'][0:1024].strip()
    session['entity'] = entity

    # Discover entity
    try: session['info'] = tentlib.discover(entity)
    except: return "An error occured while connecting to your entity (discovery failure)."

    # Check that entity is unique
    if User.where("entity=%s", (entity,)): 
        return "Error: This entity is already registered."

    # Validate Feed
    try: 
        rss = feedparser.parse(feed_url)
    except: 
        return "Error: Smoke Signals could not parse the RSS feed."

    # Create App Post
    (app_id, app_hawk_key, app_hawk_id) = tentlib.create_ss_app_post(entity)

    # Save our new user and rss feed
    user = User().create(entity, app_id, app_hawk_key, app_hawk_id)
    feed = Feed().create(feed_url, user.id)

    # Add all items in the feed to recent_items_cache, so they don't all get
    # posted the first time the feed is processed.
    initial_items = deque([], Feed.recent_items_cache_size)
    for entry in rss['entries']:
        initial_items.appendleft(Feed.hashable_entry(entry))
    feed.recent_items_cache = initial_items
    feed.save()

    # Start OAuth
    return start_oauth("/finish_registration")

@app.route('/finish_registration')
def finish_registration():
    return "Success! Smoke Signals will now post new RSS items to your Tent server."
    
def start_oauth(redirect_uri):
    session['oauth_redirect'] = redirect_uri
    if 'entity' not in session:
        return "error: entity not set"
    if 'info' not in session:
        session['info'] = tentlib.discover(session['entity'])

    user = User.where("entity=%s", args=(session['entity'],), one=True)

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

    user = User.where("entity=%s", (session['entity'],), one=True)

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
    user = User.where("entity=%s", (session['entity'],), one=True)
    user.delete()
    feeds = Feed.where("user_id=%s", (user.id,))
    for feed in feeds:
        feed.delete()

    return "Successfully deleted %s" % (user.entity)
