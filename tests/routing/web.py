# -*- coding: utf-8 -*-

from flask_apputils.routing import make_router, TemplateBlueprint

web = TemplateBlueprint('web', __name__)
route = make_router(web, __name__)

route('/', 'index')
route('/home', 'home')


def index():
    return "Index Page"


def home():
    return "Home Page"