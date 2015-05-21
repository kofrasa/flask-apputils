# -*- coding: utf-8 -*-
"""
    flask_apputils.helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""

from datetime import datetime, date, time
from logging import LoggerAdapter
from flask.globals import current_app
from flask import url_for, get_flashed_messages
from jinja2.utils import Markup


__all__ = [
    'get_flash',
    'get_logger',
    'image_tag',
    'json_value',
    'link_to',
    'parse_datetime',
    'parse_date',
    'parse_time',
    'script_tag',
    'static_file',
    'style_tag'
]


def json_value(value):
    """Convert a object to a JSON primitive value

    To support any arbitrary object, implement `to_json` or `to_dict`
    method on the object t return a valid JSON primitive

    :param value: the value to convert to a JSON primitive
    """
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    elif isinstance(value, (list, set, tuple)):
        return [json_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: json_value(value[k]) for k in value}
    elif isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
        return json_value(value.to_dict())
    elif hasattr(value, 'to_json') and callable(getattr(value, 'to_json')):
        return json_value(value.to_json())
    else:
        return str(value)


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


class CustomAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        return '%s:\t%s' % (self.extra['tag'], msg), kwargs

    def warn(self, msg, *args):
        self.warning(msg, *args)


def get_logger(tag):
    """Create a custom logger adapter that tags logged messages for `current_app.logger`

    :param tag: the tag string
    :return:
    """
    return CustomAdapter(current_app.logger, {'tag': tag}) if tag else current_app.logger


def parse_datetime(value):
    """Parse the datetime string in ISO format to a datetime object

    :param value: the datetime string
    """
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except:
            pass
    return None


def parse_date(value):
    """Parse the date string in ISO format to a date object

    :param value: the date string
    """
    for fmt in ('%Y-%m-%d', '%Y%m%d'):
        try:
            return datetime.strptime(value, fmt).date()
        except:
            pass
    return None


def parse_time(value):
    """Parse the time string

    :param value: the time string
    """
    for fmt in ('%H:%M:%S', '%H%M%S'):
        try:
            return datetime.strptime(value, fmt).date()
        except:
            pass
    return None