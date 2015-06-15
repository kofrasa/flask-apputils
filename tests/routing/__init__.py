# -*- coding: utf-8 -*-

from flask import Flask
from . import api, web


app = Flask(__name__)

app.register_blueprint(api.web)
app.register_blueprint(web.web)