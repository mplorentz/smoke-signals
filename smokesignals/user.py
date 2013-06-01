class User:
    def __init__(self, db):
        self.db = db
        self.app_mac_key_id  = None 
        self.app_id          = None 
        self.app_mac_key     = None 
        self.entity          = None 
        self.user_mac_key    = None 
        self.user_mac_key_id = None 
        self.to_protocol     = None
        self.to_post_type    = None
        self.from_post_type  = None
        self.visibility      = None

    def where(self, conditions, args=(), one=False):
        stmt = "SELECT * FROM users WHERE %s" % (conditions)
        res = self.db.query_db(stmt, args, one=one)
        #TODO fetch preferences from User's Tent 
        if not res:
            return []
        if one:
            for col, val in res.items():
                setattr(self, col, val)
            return self
        else:
            users = []
            for row in res:
                u = User(self.db)
                for col, val in row.items():
                    setattr(u, col, val)
                users.append(u)
            return users

    def find_by_entity(self, entity):
        return self.where("entity=?", (entity,), one=True)

    def create(self, entity, user_mac_key_id, user_mac_key, to_protocol, post_type, visibility):
        #TODO get the app mac_key_id from somewhere?
        app_mac_key_id = 1
        app_mac_key    = "foo"
        #TODO save to_protocol, post_type, and visibility in User's Tent
        self.db.insert(
            """INSERT INTO users (entity, user_mac_key_id, user_mac_key, app_mac_key_id, app_mac_key)
            VALUES (?, ?, ?, ?, ?)""",
            (entity, user_mac_key_id, user_mac_key, app_mac_key_id, app_mac_key)
            )

        self = User(self.db)
        setattr(self, "entity", entity)
        setattr(self, "user_mac_key_id", user_mac_key_id)
        setattr(self, "user_mac_key", user_mac_key)
        setattr(self, "app_mac_key_id", app_mac_key_id)
        setattr(self, "app_mac_key", app_mac_key)
        setattr(self, "to_protocol", to_protocol)
        setattr(self, "post_type", post_type)
        setattr(self, "visibility", visibility)
        return self
