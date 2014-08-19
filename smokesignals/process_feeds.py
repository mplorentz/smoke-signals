import json, urllib2, feedparser
from collections import deque
from models.user import User
from models.prefs import Prefs
from models.feed import Feed
from models.feed_item import FeedItem
import lib.tentlib as tentlib

def rss2tent():
    """Fetches new RSS posts and adds them to users' Tent servers"""
    
    # fetch all users
    users = User.where("'1'")
    
    for user in users:
        # fetch the user's preferences
        prefs = user.get_preferences()
        # fetch the rss feed
        try:
            rss = feedparser.parse(prefs.rss_url)
        except:
            print("Error parsing RSS feed %s" % (prefs.rss_url))
            pass

        # add new rss posts to the user's Tent server
        recent = prefs.recent_items_cache
        for entry in rss['entries']:
            # Decide if this is a new post or not
            hashable_entry = Prefs.make_hashable_entry(entry)
            if hashable_entry not in recent:    
                print("Found new item %s" % (entry['link']))
                post_func = Prefs.func_for_post_type(prefs.post_type)
                post_func(entry, user)
                recent.appendleft(hashable_entry)

        prefs.recent_items_cache = recent
        prefs.save()

def main():
    rss2tent()
   
if __name__ == "__main__" : main()
