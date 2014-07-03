from database import Database

class FeedItem:
    def __init__(self):
        self.db = Database()
        self.id = None
        self.title = None
        self.url = None
        self.published_date = None
        self.feed_id = None

    @staticmethod
    def where(conditions, args=(), one=False):
        db = Database()
        stmt = "SELECT * FROM feed_items WHERE %s" % (conditions)
        res = db.query_db(stmt, args, one=one)
        if not res:
            return []
        if one:
            f = FeedItem()
            for col, val in res.items():
                setattr(f, col, val)
            return f
        else:
            feed_items = []
            for row in res:
                f = Feed()
                for col, val in row.items():
                    setattr(f, col, val)
                feed_items.append(f)
            return feed_items

    def create(url, last_fetch_date, user_id):
        self.db.insert(
            """INSERT INTO feeds (url, last_fetch_date, user_id)
            VALUES (?, ?, ?)""",
            (url, last_fetch_date, user_id)
            )

        self = Feed()
        setattr(self, "id", self.db.conn.lastrowid)
        setattr(self, "title", title)
        setattr(self, "url", url)
        setattr(self, "published_date", published_date)
        setattr(self, "feed_id", feed_id)
        return self

    def save(self):
        self.db.insert(
            "UPDATE feed_items SET title = ?, url = ?, published_date = ?, feed_id = ? WHERE id = ?"
            (self.title, self.url, self.published_date, self.feed_id, self.id)
            )
