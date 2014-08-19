import smokesignals.lib.tentlib as tentlib
from smokesignals.models.user import User
import smokesignals.plugins as plugins
from collections import deque
import json, urllib2, pickle, base64, feedparser

class Prefs:
    post_type_to_func = {
        "status": plugins.status.post_status,
        "essay":  plugins.essay.post_essay,
    }

    def __init__(self, entity):
        self.post_id = None
        self.version_id = None
        self.source_protocol = None
        self.post_type = None
        self.rss_url = None
        self.recent_items_cache = None
        self.entity = entity

    @staticmethod
    def get_for_user(user):
        prefs = Prefs(user.entity)
        info = tentlib.discover(user.entity)
        if user.preferences_post:
            post_url = info['post']['content']['servers'][0]['urls']['post']
            post_url = post_url.replace('{entity}', user.entity).replace('{post}', user.preferences_post)
            req = tentlib.form_request(post_url, '', user.app_id, user.hawk_key, user.hawk_id)
            try:
                res = json.load(urllib2.urlopen(req))
                prefs.post_id = user.preferences_post
                prefs.version_id = res["post"]["version"]["id"]
                cont = res['post']['content']
                prefs.source_protocol = cont['source_protocol']
                prefs.rss_url = cont['rss_url']
                prefs.post_type = cont['post_type']
                prefs.recent_items_cache = pickle.loads(base64.b64decode(cont['recent_items_cache']))
            except urllib2.HTTPError, err:
                print(err.read())
                print(err.message)
        else:
            prefs.recent_items_cache = deque([], 200)

        return prefs

    def save(self):
        info = tentlib.discover(self.entity)
        user = User.where("entity = %s", (self.entity,), one=True)
        post_type = 'http://mattlorentz.com/tent/types/smoke-signals-prefs/v0#'
        req = None

        if self.post_id and self.version_id:
            # Create a new version
            post_url = info['post']['content']['servers'][0]['urls']['post']
            post_url = post_url.replace('{entity}', self.entity).replace('{post}', self.post_id)

            body = {
                'id': self.post_id,
                'entity': self.entity,
                'type': post_type,
                'content': {
                    'source_protocol': self.source_protocol,
                    'post_type': self.post_type,
                    'rss_url': self.rss_url,
                    'recent_items_cache': base64.b64encode(pickle.dumps(self.recent_items_cache, 2)),
                },
                'version': {
                    'parents': [
                        {'version': self.version_id},
                    ],
                },
            }

            req = tentlib.form_request(post_url, body, user.app_id, user.hawk_key, user.hawk_id, http_verb="PUT", post_type=post_type)
        else: 
            # Populate the recent_items cache so we don't flood the user's feed.
            rss = feedparser.parse(self.rss_url)
            for entry in rss['entries']:
                self.recent_items_cache.appendleft(Prefs.make_hashable_entry(entry))

            # Create new preferences post
            post_url = info['post']['content']['servers'][0]['urls']['new_post']
            body = {
                'type': post_type,
                'content': {
                    'source_protocol': self.source_protocol,
                    'post_type': self.post_type,
                    'rss_url': self.rss_url,
                    'recent_items_cache': base64.b64encode(pickle.dumps(self.recent_items_cache, 2)),
                },
            }
            req = tentlib.form_request(post_url, body, user.app_id, user.hawk_key, user.hawk_id, post_type=post_type)

        # Post to the user's server
        try:
            res = json.load(urllib2.urlopen(req))
            self.post_id = res['post']['id']
            self.version_id = res['post']['version']['id']
            user.preferences_post = self.post_id
            user.save()
        except urllib2.HTTPError, err:
            print(err.read())
            print(err.message)
            raise(err)

    @staticmethod
    def expand(entity, d):
        """ Takes a dict with Prefs attributes as keys, and returns a Prefs object
            and an error message (if any). Also validates the given values. Does 
            not accept values for post_id, version_id, or recent_items_cache."""
        user = User.where("entity=%s", (entity,), one=True)
        prefs = user.get_preferences()
        
        if d['source_protocol'] and d['source_protocol'] not in ["tent", "rss"]:
            return {}, "Invalid source protocol %s." % (d['source_protocol'])
        if d['post_type'] and d['post_type'] not in Prefs.post_type_to_func.keys():
            return {}, "Invalid post type %s." % (d['post_type'])
        try: 
            rss = feedparser.parse("rss_url")
        except: 
            return "Error: Smoke Signals could not parse the RSS feed."

        prefs.source_protocol = d["source_protocol"]
        prefs.post_type = d["post_type"]
        prefs.rss_url = d["rss_url"]

        return prefs, None

    @staticmethod
    def func_for_post_type(post_type):
        """ Takes a valid post type and returns a function that takes an rss_entry 
            and user and posts the rss_entry to the user's Tent server."""
        func = Prefs.post_type_to_func.get(post_type, None)
        if func:
            return func
        else:
            print("Error: could not get post function for %s post type." % (post_type))
            return lambda x, y : x



    @staticmethod
    def make_hashable_entry(entry):
        """Takes an entry from a feedparser RSS feed and produces a hashable value"""
        return (entry['link'], entry['title'], entry['published'])
