from lib.database import Database

class User:
    def __init__(self):
        self.db              = Database()
        self.id              = None
        self.entity          = None 
        self.app_id          = None 
        self.app_hawk_key    = None 
        self.app_hawk_id     = None 
        self.hawk_key        = None
        self.hawk_id         = None

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
        return User.where("entity=%s", (entity,), one=True)

    @staticmethod
    def create(entity, app_id, app_hawk_key, app_hawk_id):
        self = User()
        self.db.insert(
            """INSERT INTO users (entity, app_id, app_hawk_key, app_hawk_id)
            VALUES (%s, %s, %s, %s) RETURNING id""",
            (entity, app_id, app_hawk_key, app_hawk_id)
            )

        setattr(self, "id", self.db.cursor.fetchone()[0])
        setattr(self, "entity", entity)
        setattr(self, "app_id", app_id)
        setattr(self, "app_hawk_key", app_hawk_key)
        setattr(self, "app_hawk_id", app_hawk_id)
        setattr(self, "hawk_key", None)
        setattr(self, "hawk_id", None)
        return self

    def save(self):
        self.db.insert(
            "UPDATE users SET app_id = %s, app_hawk_key = %s, app_hawk_id = %s, hawk_key = %s, hawk_id = %s, entity = %s WHERE id = %s",
            (self.app_id, self.app_hawk_key, self.app_hawk_id, self.hawk_key, self.hawk_id, self.entity, self.id)
            )

    def delete(self):
        self.db.insert("DELETE FROM users WHERE id=%s", (self.id,))
