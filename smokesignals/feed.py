from database import Database

class Feed:
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
                setattr(f, col, val)
            return f
        else:
            feeds = []
            for row in res:
                f = Feed()
                for col, val in row.items():
                    setattr(f, col, val)
                feeds.append(f)
            return feeds

    def create(url, last_fetch_date, user_id):
        self.db.insert(
            """INSERT INTO feeds (url, last_fetch_date, user_id)
            VALUES (?, ?, ?)""",
            (url, last_fetch_date, user_id)
            )

        self = Feed()
        setattr(self, "id", self.db.conn.lastrowid)
        setattr(self, "url", url)
        setattr(self, "last_fetch_date", last_fetch_date)
        setattr(self, "user_id", user_id)
        return self

    def save(self):
        self.db.insert(
            "UPDATE feeds SET url = ?, last_fetch_date = ?, user_id = ? WHERE id = ?",
            (self.url, self.last_fetch_date, self.user_id, self.id)
            )
