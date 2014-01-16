from flask import Flask, request, g, render_template, redirect, session
import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse
import feedparser
from user import User
from database import Database

Flask.secret_key = "ITSASECRETDONTTELLANYONE"

def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

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
        """ Go through the Tent auth process. """
        # TODO validate form input
        entity = request.form['entity'].strip()
        if entity[-1] == "/":
            entity = entity[:-1]
        session['entity'] = entity
        to_protocol = request.form['to_protocol']
        post_type = request.form['post_type']
        visibility = request.form['visibility']


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
        app_post_res = urllib2.urlopen(req)
        app_post = json.loads(app_post_res.read())

        # get the id from the app post
        session['client_id'] = app_post['post']['id']

        # get the hawk key and id from the credentials post
        cred_url = re.match(r"<(.*)>;", app_post_res.headers.getheader('link')).group(1)
        app_cred_post = json.load(urllib2.urlopen(cred_url))
        session['access_token_key'] = app_cred_post['post']['content']['hawk_key']
        session['access_token_id']  = app_cred_post['post']['id']

        # save our new user
        user = User(g.db)
        user.create(entity, session['acess_token_id'], session['access_token_key'], to_protocol, post_type, visibility)
        g.db.conn.commit()

        #start OAuth
        return start_oauth()
        
    def start_oauth():
        if 'entity' not in session:
            return "error: entity not set"
        if ('access_token_key' not in session) or ('access_token_id' not in session):
            user = User(g.db)
            user = user.where("entity=?", (session['entity'],), one=True)
            session['access_token_key'] = user.user_mac_key
            session['access_token_id']  = user.user_mac_key_id
        if 'info' not in session:
            res = urllib2.urlopen(entity)
            link = re.match(r"<(.*)>;", res.headers.getheader('link')).group(1)
            session['info'] = json.load(urllib2.urlopen(entity + link))      
            
        oauth_url = session['info']['post']['content']['servers'][0]['urls']['oauth_auth']
        state = randomword(10)
        session['state'] = state

        return redirect("%s?client_id=%s&state=%s" % (oauth_url, session['client_id'], state))

    @app.route('/finish_auth')
    def finish_auth():
        code = request.args.get('code')
        state = request.args.get('state')

        # verify the state
        if state != session['state']:
            return "states did not match up"

        token_url = session['info']['post']['content']['servers'][0]['urls']['oauth_token']
        payload = {"code": code, "token_type": "https://tent.io/oauth/hawk-token"}
        req = form_request(token_url, payload, session['client_id'], session['access_token_key'], session['access_token_id'])

        try:
            res = json.load(urllib2.urlopen(req))
        except urllib2.HTTPError, err:
            print(err.read())
            return "an error occured during authorization"

        session['access_token'] = res['access_token']
        session['hawk_key'] = res['hawk_key']

        return res['access_token']


    return app
    
def form_request(url, body, client_id, hawk_key, hawk_id):
    urlparts = urlparse.urlparse(url)
    host = urlparts.netloc
    uri = urlparts.path
    port = 0
    if (urlparts.scheme == "https"):
        port = 443
    elif (urlparts.scheme == "http"):
        port = 80
    now   = str(int(time.time()))
    nonce = randomword(10)
    mac_data = "hawk.1.header\n%s\n%s\nPOST\n%s\n%s\n%s\n\n\n%s\n\n" % (
            now, nonce, uri, host, port, client_id
    )

    mac = base64.b64encode(hmac.new(hawk_key.encode('utf-8'), mac_data, hashlib.sha256).digest())

    req = urllib2.Request(
        url, 
        data=json.dumps(body),
        headers={
            'Content-Type':'application/json',
            'Authorization': 'Hawk id="%s", mac="%s", ts="%s", nonce="%s", app="%s"' %
                (hawk_id, mac, now, nonce, client_id)
        }
    )

    return req

if __name__ == '__main__':
    app = create_app()
    app.run()

