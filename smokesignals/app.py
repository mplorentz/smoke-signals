import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse, feedparser
from flask import Flask, request, g, render_template, redirect, session
from models.user import User
from models.feed import Feed
from lib.database import Database
import lib.tentlib as tentlib

Flask.secret_key = "ITSASECRETDONTTELLANYONE"

def create_app():
    app = Flask(__name__)
    app.debug = True
    
    @app.before_request
    def before_request():
        g.db = Database()

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db'):
            del(g.db)

    # define all the routes here

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
        if User.where("entity=?", (entity,)): 
            return "Error: This entity is already registered."

        # Validate Feed
        try: feedparser.parse(feed_url)
        except: return "Error: Smoke Signals could not parse the RSS feed."

        # Create App Post
        (app_id, app_hawk_key, app_hawk_id) = tentlib.create_ss_app_post(entity)

        # Save our new user and rss feed
        user = User().create(entity, app_id, app_hawk_key, app_hawk_id)
        feed = Feed().create(feed_url, user.id)

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
        feeds = Feed.where("user_id=?", (user.id,))
        for feed in feeds:
            feed.delete()

        return "Successfully deleted %s" % (user.entity)

    return app
    

if __name__ == '__main__':
    app = create_app()
    app.run()

