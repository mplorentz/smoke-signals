from flask import Flask, request, g, render_template, redirect, session
import json, urllib2, re, random, string, time, hmac, hashlib, base64
import feedparser
from database import Database

Flask.secret_key = "ITSASECRETDONTTELLANYONE"

def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

def create_app():
    app = Flask(__name__)
    app.debug = True
    
    @app.before_request
    def before_request():
        db = Database()

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
        return redirect("/start_auth?entity=%s" % (request.form['entity']))

    @app.route('/start_auth')
    def start_auth():
        """ Go through the Tent auth process. """
        entity = request.args.get('entity')
        if entity[-1] == "/":
            entity = entity[:-1]
        session['entity'] = entity

        # Discover the given entity
        res = urllib2.urlopen(entity)
        link = re.match(r"<(.*)>;", res.headers.getheader('link')).group(1)
        info = json.load(urllib2.urlopen(entity + link))
        session['info'] = info

        # Create an app post
        new_post_url = info['post']['content']['servers'][0]['urls']['new_post']
        # TODO the url of the app needs to be set in a config file
        # and used in the redirect_uri
        new_post = {
            "type": "https://tent.io/types/app/v0#",
            "content": {
                "name": "Smoke Signals",
                "url": "https:/://github.com/mplorentz/smoke-signals",
                "types": {
                    "read": [
                        "https://tent.io/types/app/v0",
                        "https://tent.io/types/status/v0",
                    ],
                    "write": [
                        "https://tent.io/types/status/v0"
                    ]
                },
                "redirect_uri": "http://localhost:5000/finish_auth"
            },
            "permissions": {
                "public": False
            }
        }
        data = json.dumps(new_post)
        req = urllib2.Request(
            new_post_url, 
            data=data,
            headers={
                'Content-Type':'application/vnd.tent.post.v0+json; type="https://tent.io/types/app/v0#"',
                'Content-Length': len(data),
            }
        )
        res = urllib2.urlopen(req)
        token_url = re.match(r"<(.*)>;", res.headers.getheader('link')).group(1)
        app_cred_post = json.load(urllib2.urlopen(token_url))
        app_post_id = app_cred_post['post']['mentions'][0]['post']
        session['client_id'] = app_post_id
        session['hawk_key'] = app_cred_post['post']['content']['hawk_key']
        session['hawk_id']  = app_cred_post['post']['id']

        #start OAuth
        oauth_url = info['post']['content']['servers'][0]['urls']['oauth_auth']
        state = randomword(10)
        session['state'] = state
        return redirect("%s?client_id=%s&state=%s" % (oauth_url, app_post_id, state))

    @app.route('/finish_auth')
    def finish_auth():
        code = request.args.get('code')
        state = request.args.get('state')

        # verify the state
        if state != session['state']:
            return "states did not match up"

        token_url = session['info']['post']['content']['servers'][0]['urls']['oauth_token']
        now   = str(int(time.time()))
        nonce = randomword(10)
        uri   = token_url.replace(session['entity'], "")
        host  = session['entity'][7:]
        mac_data = "hawk.1.header\n%s\n%s\nPOST\n%s\n%s\n80\n\n\n%s\n\n" % (
                now, nonce, uri, host, session['client_id']
        )
        print(mac_data)
        mac = base64.b64encode(hmac.new(session['hawk_key'].encode('utf-8'), mac_data, hashlib.sha256).digest())

        req = urllib2.Request(
            token_url, 
            data=json.dumps({"code": code, "token_type": "https://tent.io/oauth/hawk-token"}),
            headers={
                'Content-Type':'application/json',
                'Authorization': 'Hawk id="%s", mac="%s", ts="%s", nonce="%s", app="%s"' %
                    (session['hawk_id'], mac, now, nonce, session['client_id'])
            }
        )

        res = json.load(urllib2.urlopen(req))

        return res['access_token']

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()

