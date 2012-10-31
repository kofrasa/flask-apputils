# -*- coding: utf-8 -*-

from flask import g, url_for, get_flashed_messages
from flaskext.htmlbuilder import html

__all__ = [
    'static',
    'get_flash',
    'link_to',
    'image_tag',
    'style_tag',
    'script_tag',
    'ctx_set',
    'ctx_get',
    'ctx_clear',
    'ctx_dump'
]


# manually managed local context for passing variables across modules
_ctx_data = {}

def ctx_get(key):
    global _ctx_data
    return _ctx_data.get(key, None)

def ctx_set(key, value):
    global _ctx_data
    _ctx_data[key] = value

def ctx_clear(key=None):
    global _ctx_data
    if key:
        _ctx_data.pop(key,None)
    else:
        _ctx_data.clear()

def ctx_dump():
    global _ctx_data
    print "-- Context Dump --"
    for k in _ctx_data:
        print "%s:\t%r" % (k, _ctx_data[k])
    print "------------------"


def static(filename):
    return url_for('static', filename=filename)


def get_flash(category=None, sep='\n'):
    if not category:
        return sep.join(get_flashed_messages())
    messages = get_flashed_messages(with_categories=True)
    return sep.join([m for k,m in messages if k == category])


def link_to(text, endpoint, **kwargs):
    try:
        url = url_for(endpoint)
        endpoint = url
    except:
        pass
    return unicode(html.a(href=endpoint, **kwargs)(text))


def style_tag(filename, **kwargs):
    """Creates a link tag to a CSS stylesheet file.
    The extension '.css' is added by default if the `filename` is missing one.

    By default files are sent from the 'css' subdirectory in the static folder
    To link to files outside of that folder, specify an absolute path such as,
    '/twitter/css/bootstrap.css'. The root folder is assumed to be under
    the static folder and the correct path is generated accordingly.

    '/static/twitter/css/boostrap.css'
    """
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'css/' +  filename

    if not filename.endswith('.css'):
        filename += '.css'

    for k in ('rel','type','href'):
        kwargs.pop(k,None)

    return unicode(html.link(rel='stylesheet', type="text/css", href=static(filename), **kwargs))


def script_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'js/' +  filename
    if not filename.endswith('.js'):
        filename += '.js'

    return unicode(html.script(type="text/javascript",
                               src=static(filename), **kwargs)())


def image_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'img/' +  filename

    return unicode(html.img(src=static(filename), **kwargs))
