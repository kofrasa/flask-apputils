# -*- coding: utf-8 -*-
"""
    flask_apputils.templating
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Template utilities to inject into the application context processor for rails-style template helpers
"""

from flask.globals import current_app
from flask import url_for, get_flashed_messages
from jinja2.utils import Markup

__all__ = [
    'static_file',
    'get_flash',
    'link_to',
    'image_tag',
    'style_tag',
    'script_tag'
]


def init_context_processor(app):
    """Update the :class:`Flask` instance context processors

    :param app: a Flask application instance
    """
    app.context_processor(lambda: {
        'static_file': static_file,
        'get_flask': get_flash,
        'link_to': link_to,
        'style_tag': style_tag,
        'script_tag': script_tag,
        'image_tag': image_tag,
    })


def static_file(filename):
    """Return a link to a file from the current app `STATIC_FOLDER`"""
    return url_for(current_app.static_folder, filename=filename, _external=True)


def get_flash(category=None, sep='\n'):
    """Get selective formatted flash messages

    :param category: category
    :param sep: separator for multiple messages
    """
    if not category:
        return sep.join(get_flashed_messages())
    return sep.join([m for k, m in get_flashed_messages(with_categories=True) if k == category])


def link_to(text, endpoint, **kwargs):
    """Generates an HTML `a` tag with links"""
    try:
        url = url_for(endpoint, _external=True)
        endpoint = url
    except:
        pass
    kwargs["href"] = endpoint
    return Markup("<a %s>%s</a>" % (_format_attr(**kwargs), text))


def style_tag(filename, **kwargs):
    """Generates an HTML `link` tag to a CSS stylesheet file.
    The extension '.css' is added by default if missing.

    Files are served from the `css` subdirectory in the static folder.
    """
    filename = "css/%s" % filename
    if not filename.endswith('.css'):
        filename += '.css'

    kwargs["rel"] = "stylesheet"
    kwargs["type"] = "text/css"
    kwargs["href"] = static_file(filename)

    return Markup("<link %s/>" % _format_attr(**kwargs))


def script_tag(filename, **kwargs):
    """Generates an HTML `script` tag.

    Files are service from `js` subdirectory in the static folder
    """

    filename = "js/%s" % filename
    if not filename.endswith('.js'):
        filename += '.js'

    kwargs['src'] = static_file(filename)
    kwargs['type'] = "text/javascript"

    return Markup("<script %s></script>" % _format_attr(**kwargs))


def image_tag(filename, **kwargs):
    """Generate an HTML `img` tag.

    Files are served from the `images` subdirectory in the static folder
    """
    filename = "images/%s" % filename
    kwargs['src'] = static_file(filename)
    return Markup("<img %s>" % _format_attr(**kwargs))


def _format_attr(**kwargs):
    attr = []
    for key, value in kwargs.items():
        attr.append("%s=\"%s\"" % (key, value))
    return " ".join(attr)