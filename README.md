*Smoke signals is no longer being developed. If you'd like to take over development, please fork this project and get in touch.*

Smoke-signals is a Tent<->RSS bridge designed to pull RSS feeds into the Tent ecosystem and publish Tent content in the RSS format.

Find out more about [Tent](http://tent.io)

## Installation

Setup a virtualenv:

    mkvirtualenv ssenv
    pip install -r requirements.txt

Make your database:

    sqlite3 db/smokesignals.db < db/schema.sqlite3

And get 'er started:

    python smokesignals/app.py
