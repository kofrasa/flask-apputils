# -*- coding: utf-8 -*-

from flask.globals import current_app as app
from flask import g, url_for, get_flashed_messages
from flaskext.htmlbuilder import html
from jinja2.utils import Markup

__all__ = [
    'static',
    'get_flash',
    'link_to',
    'image_tag',
    'style_tag',
    'script_tag'
]

def static(filename):
    folder = app.config.get('STATIC_FOLDER', 'static')
    return url_for(folder, filename=filename)


def get_flash(category=None, sep='\n'):
    if not category:
        return sep.join(get_flashed_messages())
    messages = get_flashed_messages(with_categories=True)
    return sep.join([m for k,m in messages if k == category])


def link_to(text, endpoint, **kwargs):
    try:
        kwargs['_external'] = True
        url = url_for(endpoint, **kwargs)
        endpoint = url
    except:
        pass
    return Markup(html.a(href=endpoint, **kwargs)(text))


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

    return Markup(html.link(rel='stylesheet', type="text/css", href=static(filename), **kwargs))


def script_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'js/' +  filename
    if not filename.endswith('.js'):
        filename += '.js'

    return Markup(html.script(type="text/javascript",
                               src=static(filename), **kwargs)())


def image_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'img/' +  filename
    return Markup(html.img(src=static(filename), **kwargs))
