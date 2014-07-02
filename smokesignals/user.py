from database import Database

class User:
    def __init__(self):
        self.db              = Database()
        self.app_id          = None 
        self.entity          = None 
        self.hawk_key        = None
        self.hawk_id         = None
        self.to_protocol     = None
        self.to_post_type    = None
        self.from_post_type  = None
        self.visibility      = None

    @staticmethod
    def where(conditions, args=(), one=False):
        db = Database()
        stmt = "SELECT * FROM users WHERE %s" % (conditions)
        res = db.query_db(stmt, args, one=one)
        #TODO fetch preferences from User's Tent 
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
                u = User(self.db)
                for col, val in row.items():
                    setattr(u, col, val)
                users.append(u)
            return users

    def find_by_entity(entity):
        db = Database()
        return User.where("entity=?", (entity,), one=True)

    def create(self, entity, app_id, hawk_key, hawk_id, to_protocol, post_type, visibility):
        #TODO save to_protocol, post_type, and visibility in User's Tent
        self.db.insert(
            """INSERT INTO users (entity, app_id, hawk_key, hawk_id)
            VALUES (?, ?, ?, ?)""",
            (entity, app_id, hawk_key, hawk_id)
            )

        self = User()
        setattr(self, "entity", entity)
        setattr(self, "app_id", app_id)
        setattr(self, "hawk_key", hawk_key)
        setattr(self, "hawk_id", hawk_id)
        setattr(self, "to_protocol", to_protocol)
        setattr(self, "post_type", post_type)
        setattr(self, "visibility", visibility)
        return self

    def save(self):
        self.db.insert(
            "UPDATE users SET app_id = ?, hawk_key = ?, hawk_id = ? WHERE entity = ?",
            (self.app_id, self.hawk_key, self.hawk_id, self.entity)
            )
