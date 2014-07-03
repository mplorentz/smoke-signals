from database import Database

class User:
    def __init__(self):
        self.db              = Database()
        self.id              = None
        self.app_id          = None 
        self.entity          = None 
        self.hawk_key        = None
        self.hawk_id         = None
        self.feed_url        = None

    @staticmethod
    def where(conditions, args=(), one=False):
        db = Database()
        stmt = "SELECT * FROM users WHERE %s" % (conditions)
        res = db.query_db(stmt, args, one=one)
        if not res:
            return []
        if one:
            u = User()
            for col, val in res.items():
                setattr(u, col, val)
            return u
        else:
            users = []
            for row in res:
                u = User()
                for col, val in row.items():
                    setattr(u, col, val)
                users.append(u)
            return users

    def find_by_entity(entity):
        db = Database()
        return User.where("entity=?", (entity,), one=True)

    def create(self, entity, app_id, hawk_key, hawk_id):
        self.db.insert(
            """INSERT INTO users (entity, app_id, hawk_key, hawk_id)
            VALUES (?, ?, ?, ?)""",
            (entity, app_id, hawk_key, hawk_id)
            )

        self = User()
        setattr(self, "id", self.db.conn.lastrowid)
        setattr(self, "entity", entity)
        setattr(self, "app_id", app_id)
        setattr(self, "hawk_key", hawk_key)
        setattr(self, "hawk_id", hawk_id)
        return self

    def save(self):
        self.db.insert(
            "UPDATE users SET app_id = ?, hawk_key = ?, hawk_id = ?, feed_url = ?, entity = ? WHERE id = ?",
            (self.app_id, self.hawk_key, self.hawk_id, self.feed_url, self.entity, self.id)
            )
