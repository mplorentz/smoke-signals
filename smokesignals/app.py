from flask import Flask, request, g
import feedparser
from database import Database

def create_app():
    app = Flask(__name__)
    app.debug = True
    
    @app.before_request
    def before_request():
        db = Database()
        g.db = db.connect()

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

