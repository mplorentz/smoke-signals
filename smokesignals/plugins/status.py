from smokesignals.lib import tentlib
import urllib2, json

def post_status(rss_entry, user):
    info = tentlib.discover(user.entity)
    new_post_url = info['post']['content']['servers'][0]['urls']['new_post']
    post_type = "https://tent.io/types/status/v0#"
    data = {
        "type": post_type,
        "permissions": {
            "public": True,
        },
        "content": {
            "text": "[%s](%s)" % (rss_entry['title'], rss_entry['link'])
        },
    }
    req = tentlib.form_request(new_post_url, data, user.app_id, user.hawk_key, user.hawk_id, post_type=post_type)
    try:
        res = json.load(urllib2.urlopen(req))
    except urllib2.HTTPError, err:
        print(err.read())
        print(err.message)
