Smoke-signals is a Tent<->RSS bridge designed to pull RSS feeds into the Tent ecosystem and publish Tent content in the RSS format.

There is a hosted instance [here](http://smokesignalsrss.herokuapp.com)

Find out more about [Tent](http://tent.io)

## Installation

Setup a virtualenv:

    mkvirtualenv ssenv
    pip install -r requirements.txt

Make your database:

    sqlite3 db/smokesignals.db < db/schema.sqlite3

And get 'er started:

    python webserver.py & python smokesignalsd.py

## Deployment

If you want to deploy Smoke Signals yourself you may want to check out the Heroku branch. You can find detailed instructions on the [wiki](https://github.com/mplorentz/smoke-signals/wiki/Heroku).

## Post Types

It's super easy to add support for your favorite post type in Smoke Signals. Just: 
1. Add a module to the plugins folder that can post an RSS item to the user's account.
2. Add an import for your module to plugins/ __init__.py
3. Add your post type and function to the `post_type_to_func` array in models/prefs.py
4. Add a radio button for the post type to templates/preferences.html
