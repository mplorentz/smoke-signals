import psycopg2
class Database:
    def __init__(self):
        self.conn = psycopg2.connect('dbname=smokesignals')
        self.cursor = self.conn.cursor()

    def query_db(self, query, args=(), one=False):
        self.cursor.execute(query, args)
        rv = [dict((self.cursor.description[idx][0], value)
            for idx, value in enumerate(row)) for row in self.cursor.fetchall()]
        return (rv[0] if rv else None) if one else rv

    def insert(self, stmt, args=()):
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def __del__(self):
        self.conn.commit()
        self.conn.close()

