from smokesignals.lib.database import Database
import smokesignals.lib.tentlib as tentlib
import urllib2, pickle, base64, json
from collections import deque

class User:
    def __init__(self):
        self.db               = Database()
        self.id               = None
        self.entity           = None 
        self.app_id           = None 
        self.app_hawk_key     = None 
        self.app_hawk_id      = None 
        self.hawk_key         = None
        self.hawk_id          = None
        self.preferences_post = None
        self.preferences      = None

    def get_preferences(self):
        from smokesignals.models.prefs import Prefs
        self.preferences = Prefs.get_for_user(self)
        return self.preferences

    def save_preferences(self):
        from smokesignals.models.prefs import Prefs
        self.preferences.save()
        self.preferences_post = self.preferences.post_id

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

    @staticmethod
    def create(entity, app_id, app_hawk_key, app_hawk_id):
        self = User()
        self.db.insert(
            """INSERT INTO users (entity, app_id, app_hawk_key, app_hawk_id)
            VALUES (?, ?, ?, ?)""",
            (entity, app_id, app_hawk_key, app_hawk_id)
            )

        setattr(self, "id", self.db.cursor.lastrowid)
        setattr(self, "entity", entity)
        setattr(self, "app_id", app_id)
        setattr(self, "app_hawk_key", app_hawk_key)
        setattr(self, "app_hawk_id", app_hawk_id)
        setattr(self, "hawk_key", None)
        setattr(self, "hawk_id", None)
        setattr(self, "preferences_post", None)
        return self

    def save(self):
        self.db.insert(
            "UPDATE users SET app_id = ?, app_hawk_key = ?, app_hawk_id = ?, hawk_key = ?, hawk_id = ?, entity = ?, preferences_post = ? WHERE id = ?",
            (self.app_id, self.app_hawk_key, self.app_hawk_id, self.hawk_key, self.hawk_id, self.entity, self.preferences_post, self.id)
            )

    def delete(self):
        self.db.insert("DELETE FROM users WHERE id=?", (self.id,))
