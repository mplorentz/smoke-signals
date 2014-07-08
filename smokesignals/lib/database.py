import psycopg2, os, urlparse
class Database:
    def __init__(self):

        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(os.environ["DATABASE_URL"])

        self.conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

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

