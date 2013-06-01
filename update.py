import json, urllib2

def rss2tent():
    """Fetches new RSS posts and adds them to users' Tent servers"""
    
    # fetch all users who want rss2tent
    users = Users.where('to_protocol = ?', ['tent'])
    
    for user in users:
        # fetch the user's rss feed
        feed = Feed.find_by_user(user)        
        feed_json = json.load(urllib.urlopen('localhost:5000/feed?url=%s' % (feed['url'])))
        
        # add new rss posts to the user's Tent server
        recent = feed['recent_entries']
        for entry in feed_json['entries']:
            hashed_entry = Feed.hash_entry(entry)
            if hashed_entry not in recent:    
                item = FeedItem.create(entry, user)
                item.save()
                feed.add_item(item)
                
        feed.save()      

def main():
    rss2tent()
   
if __name__ == "__main__" : main()
