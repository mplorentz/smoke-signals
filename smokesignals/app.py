from flask import Flask, request, g, render_template, redirect, session
import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse
import feedparser
from user import User
from database import Database
import tentlib

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


    # need a tent registration/login route for tent v0.3

    @app.route('/feed')
    def feed():
        """ View a feed, so we know parsing is working. """
        url = request.args.get('url', '')
        if not url:
            return "no url"

        data = feedparser.parse(url)
        return str(data)

    @app.route('/register', methods=['GET'])
    def start_register():
        """ Register a new user. """
        return render_template("register.html")

    @app.route('/register', methods=['POST'])
    def end_register():
        """ Go through the tentlib auth process. """
        # TODO validate form input
        entity = request.form['entity'].strip()
        if entity[-1] == "/":
            entity = entity[:-1]
        session['entity'] = entity
        to_protocol = request.form['to_protocol']
        post_type = request.form['post_type']
        visibility = request.form['visibility']

        session['info'] = tentlib.discover(entity)

        (app_id, hawk_key, hawk_id) = tentlib.create_ss_app_post(entity)

        # save our new user
        user = User()
        user.create(entity, app_id, hawk_key, hawk_id, to_protocol, post_type, visibility)
        g.db.conn.commit()

        #start OAuth
        return start_oauth()
        
    def start_oauth():
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
            return "states did not match up"

        user = User.where("entity=?", (session['entity'],), one=True)

        token_url = session['info']['post']['content']['servers'][0]['urls']['oauth_token']
        payload = {"code": code, "token_type": "https://tent.io/oauth/hawk-token"}
        req = tentlib.form_request(token_url, payload, user.app_id, user.hawk_key, user.hawk_id)

        try:
            res = json.load(urllib2.urlopen(req))
        except urllib2.HTTPError, err:
            print(err.read())
            foobar;
            return "an error occured during authorization"

        user.hawk_key = res['hawk_key']
        user.hawk_id = res['access_token']
        user.save()

        return "Success!"


    return app
    

if __name__ == '__main__':
    app = create_app()
    app.run()

