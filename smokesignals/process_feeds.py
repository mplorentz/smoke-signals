import json, urllib2, feedparser
from collections import deque
from models.user import User
from models.feed import Feed
from models.feed_item import FeedItem
import lib.tentlib as tentlib

def rss2tent():
    """Fetches new RSS posts and adds them to users' Tent servers"""
    
    # fetch all feeds
    feeds = Feed.where("1")
    
    for feed in feeds:
        # fetch the user and feed
        user = User.where("id=?", (feed.id,), one=True)
        try:
            rss = feedparser.parse(feed.url)
        except:
            print("Error parsing RSS feed %s" % (feed.url))
            pass

        
        # add new rss posts to the user's Tent server
        recent = feed.recent_items_cache
        for entry in rss['entries']:
            # Decide if this is a new post or not
            hashable_entry = Feed.hashable_entry(entry)
            if hashable_entry not in recent:    
                print("Found new item %s" % (entry['link']))
                info = tentlib.discover(user.entity)
                new_post_url = info['post']['content']['servers'][0]['urls']['new_post']
                data = {
                    "type": "https://tent.io/types/status/v0#",
                    "permissions": {
                        "public": True,
                    },
                    "content": {
                        "text": "[%s](%s)" % (entry['title'], entry['link'])
                    },
                }
                req = tentlib.form_request(new_post_url, data, user.app_id, user.hawk_key, user.hawk_id)
                try:
                    res = json.load(urllib2.urlopen(req))
                except urllib2.HTTPError, err:
                    print(err.read())
                    print(err.message)
                
                recent.appendleft(hashable_entry)

        feed.recent_items_cache = recent
        feed.save()

def main():
    rss2tent()
   
if __name__ == "__main__" : main()
