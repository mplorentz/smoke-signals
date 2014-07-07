from lib.database import Database
from collections import deque
import pickle, sqlite3

class Feed:
    recent_items_cache_size = 200

    def __init__(self):
        self.db = Database()
        self.id = None
        self.url = None
        self.last_fetch_date = None
        self.user_id = None
        self.recent_items_cache = None

    @staticmethod
    def where(conditions, args=(), one=False):
        db = Database()
        stmt = "SELECT * FROM feeds WHERE %s" % (conditions)
        res = db.query_db(stmt, args, one=one)
        if not res:
            return []
        if one:
            f = Feed()
            for col, val in res.items():
                if col == "recent_items_cache":
                    setattr(f, col, pickle.loads(str(val)))
                else:
                    setattr(f, col, val)
            return f
        else:
            feeds = []
            for row in res:
                f = Feed()
                for col, val in row.items():
                    if col == "recent_items_cache":
                        setattr(f, col, pickle.loads(str(val)))
                    else:
                        setattr(f, col, val)
                feeds.append(f)
            return feeds

    @staticmethod
    def create(url, user_id):
        self = Feed()
        self.db.insert(
            """INSERT INTO feeds (url, last_fetch_date, user_id, recent_items_cache)
            VALUES (?, ?, ?, ?)""",
            (url, 0, user_id, sqlite3.Binary(pickle.dumps(deque([], self.recent_items_cache_size), 2)))
            )

        setattr(self, "id", self.db.cursor.lastrowid)
        setattr(self, "url", url)
        setattr(self, "last_fetch_date", 0)
        setattr(self, "user_id", user_id)
        setattr(self, "recent_items_cache", deque([], self.recent_items_cache_size))
        return self

    def save(self):
        self.db.insert(
            "UPDATE feeds SET url = ?, last_fetch_date = ?, user_id = ?, recent_items_cache = ? WHERE id = ?",
            (self.url, self.last_fetch_date, self.user_id, sqlite3.Binary(pickle.dumps(self.recent_items_cache, 2)), self.id)
            )

    @staticmethod
    def hashable_entry(entry):
        """Takes an entry from a feedparser RSS feed and produces a hashable value"""
        return (entry['link'], entry['title'], entry['published'])

    def delete(self):
        self.db.insert("DELETE FROM feeds WHERE id=?", (self.id,))
