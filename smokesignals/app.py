from flask import Flask, request, g
import sqlite3
import feedparser

def create_app():
    app = Flask(__name__)

    def connect_db():
        return sqlite3.connect('db/smokesignals.db')

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db'):
            g.db.close()

    # define all the routes here

    @app.route('/')
    def main():
        """ Main landing page. """
        return "smoke signals connect tent and rss!"


    # need a tent registration/login route for tent v0.3

    @app.route('/feed')
    def feed():
        """ View a feed, so we know parsing is working. """
        url = request.args.get('url', '')
        if not url:
            return "no url"

        data = feedparser.parse(url)
        return str(data)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()

