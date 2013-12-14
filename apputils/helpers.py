# -*- coding: utf-8 -*-

from flask.globals import current_app as app
from flask import url_for, get_flashed_messages
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
    return url_for(folder, filename=filename, _external=True)


def get_flash(category=None, sep='\n'):
    if not category:
        return sep.join(get_flashed_messages())
    messages = get_flashed_messages(with_categories=True)
    return sep.join([m for k, m in messages if k == category])


def link_to(text, endpoint, **kwargs):
    try:
        url = url_for(endpoint, _external=True)
        endpoint = url
    except:
        pass
    kwargs["href"] = endpoint
    return Markup("<a %s>%s</a>" % (_format_attr(**kwargs), text))


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
        filename = 'css/' + filename

    if not filename.endswith('.css'):
        filename += '.css'

    kwargs["rel"] = "stylesheet"
    kwargs["type"] = "text/css"
    kwargs["href"] = static(filename)

    return Markup("<link %s/>" % _format_attr(**kwargs))


def script_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'js/' + filename
    if not filename.endswith('.js'):
        filename += '.js'

    kwargs['src'] = static(filename)
    kwargs['type'] = "text/javascript"

    return Markup("<script %s></script>" % _format_attr(**kwargs))


def image_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'images/' + filename
    kwargs['src'] = static(filename)
    return Markup("<img %s>" % _format_attr(**kwargs))


def _format_attr(**kwargs):
    attr = []
    for key, value in kwargs.items():
        attr.append("%s=\"%s\"" % (key, value))
    return " ".join(attr)