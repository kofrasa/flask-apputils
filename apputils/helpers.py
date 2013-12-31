# -*- coding: utf-8 -*-

from flask.globals import current_app as app
from flask import url_for, get_flashed_messages
from jinja2.utils import Markup
from werkzeug.utils import import_string, cached_property
from flask.blueprints import Blueprint

__all__ = [
    'static_file',
    'get_flash',
    'link_to',
    'image_tag',
    'style_tag',
    'script_tag',
    'LazyView',
    'create_router',
    'APIBlueprint',
    'TemplateBlueprint'
]


class LazyView(object):
    def __init__(self, import_name):
        self.__module__, self.__name__ = import_name.rsplit('.', 1)
        self.import_name = import_name

    @cached_property
    def view(self):
        return import_string(self.import_name)

    def __call__(self, *args, **kwargs):
        return self.view(*args, **kwargs)


def create_router(blueprint, module_name):
    names = []

    def router(url_rule, import_name, **options):
        view = LazyView(module_name + "." + import_name)
        # generate endpoint to handle multiple import names
        # this necessary to allow clean looking urls (no trailing slash)
        names.append(import_name)
        if import_name in names:
            endpoint = import_name + "_" + str(names.count(import_name))
        else:
            endpoint = import_name
        # register url
        blueprint.add_url_rule(url_rule, endpoint, view_func=view, **options)
    return router


class APIBlueprint(Blueprint):
    """Blueprint which serialized response to JSON and also inject request parameters as keyword arguments
    """
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        from .decorators import as_json, with_request
        view_func = as_json(with_request(view_func))
        return super(APIBlueprint, self).add_url_rule(rule, endpoint, view_func, **options)


class TemplateBlueprint(Blueprint):
    """Blueprint which automatically load and render template from templates directory
    """
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        from .decorators import templated
        # wrap with template loader function
        tpl_func = templated(self.name, view_func.__name__)
        view_func = tpl_func(view_func)
        # endpoint = options.pop("endpoint", view_func.__name__)
        return super(TemplateBlueprint, self).add_url_rule(rule, endpoint, view_func, **options)


def static_file(filename):
    return url_for(app.config.get('STATIC_FOLDER') or 'static', filename=filename, _external=True)


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
    kwargs["href"] = static_file(filename)

    return Markup("<link %s/>" % _format_attr(**kwargs))


def script_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'js/' + filename
    if not filename.endswith('.js'):
        filename += '.js'

    kwargs['src'] = static_file(filename)
    kwargs['type'] = "text/javascript"

    return Markup("<script %s></script>" % _format_attr(**kwargs))


def image_tag(filename, **kwargs):
    # support third-party libraries by using absolute path from static folder
    if filename.startswith('/'):
        filename = ''.join(filename[1:])
    else:
        filename = 'images/' + filename
    kwargs['src'] = static_file(filename)
    return Markup("<img %s>" % _format_attr(**kwargs))


def _format_attr(**kwargs):
    attr = []
    for key, value in kwargs.items():
        attr.append("%s=\"%s\"" % (key, value))
    return " ".join(attr)