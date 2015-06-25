# -*- coding: utf-8 -*-

from flask_apputils.routing import get_router, TemplateBlueprint

web = TemplateBlueprint('web', __name__)
route = get_router(web, __name__)

route('/', 'index')
route('/home', 'home')


def index():
    return "Index Page"


def home():
    return "Home Page"