import sqlite3
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('db/smokesignals.db')
        self.cursor = self.conn.cursor()

    def query_db(self, query, args=(), one=False):
        cur = self.conn.execute(query, args)
        rv = [dict((cur.description[idx][0], value)
                for idx, value in enumerate(row)) for row in cur.fetchall()]
        return (rv[0] if rv else None) if one else rv

    def insert(self, stmt, args=()):
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def __del__(self):
        self.conn.commit()
        self.conn.close()

