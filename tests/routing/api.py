# -*- coding: utf-8 -*-

from flask_apputils.routing import get_router, APIBlueprint

web = APIBlueprint('api', __name__)


def log(f):
    def wrapper(*args, **kwargs):
        print "log params: %s" % args
        return f(*args, **kwargs)
    return wrapper

route = get_router(web, __name__, filters=[log])

route('/user', 'user')
route('/student', 'student')


def user():
    return dict(name='John', age=32)


def student():
    return dict(name='Ama', form=3)
