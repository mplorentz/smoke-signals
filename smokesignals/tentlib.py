import json, urllib2, re, random, string, time, hmac, hashlib, base64, urlparse
from user import User

def new_status_post(user, text):
    datastr = json.dumps(data)
    req = urllib2.Request(
        url,
        data = datastr,
        headers = {
            'Content-Type':('application/vnd.tent.post.v0+json; %s' % data.type),
            'Content-Length': len(datastr),
        }
    )

    return urllib2.urlopen(req)
    

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
            'Content-Type': 'application/vnd.tent.post.v0+json; type="https://tent.io/types/status/v0#"',
            'Authorization': 'Hawk id="%s", mac="%s", ts="%s", nonce="%s", app="%s"' %
                (hawk_id, mac, now, nonce, client_id)
        }
    )

    return req

def form_oauth_request(url, body, client_id, hawk_key, hawk_id):
    req = form_request(url, body, client_id, hawk_key, hawk_id)
    req.headers['Content-type'] = 'application/json'
    return req

def create_ss_app_post(entity):
    """ Takes an entity and creates an app post for Smoke Signals on that entity's server.
        Returns the app's app id, Hawk key, and Hawk id."""
    info = discover(entity)

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
                    "http://mattlorentz.com/tent/types/rssfeed/v0",
                ],
                "write": [
                    "https://tent.io/types/status/v0",
                    "http://mattlorentz.com/tent/types/rssfeed/v0",
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
    app_id = app_post['post']['id']

    # get the hawk key and id from the credentials post
    cred_url = re.match(r"<(.*)>;", app_post_res.headers.getheader('link')).group(1)
    app_cred_post = json.load(urllib2.urlopen(cred_url))
    hawk_key = app_cred_post['post']['content']['hawk_key']
    hawk_id  = app_cred_post['post']['id']

    return (app_id, hawk_key, hawk_id)

def discover(entity):
    """Performs discovery on a given entity and returns the info post json."""
    res = urllib2.urlopen(entity)
    link = re.match(r"<(.*)>;", res.headers.getheader('link')).group(1)
    return json.load(urllib2.urlopen(entity + link))

def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

