from flask import Flask
app = Flask(__name__)
debug = True

import smokesignals.views
