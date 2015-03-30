#!-*- coding: utf-8 -*-
"""
    flask_apputils.routing
    ~~~~~~~~~~~~~~~~~~~~~~

    Utilities for building routing handlers
"""

from werkzeug.utils import import_string, cached_property
from flask.blueprints import Blueprint
from .decorators import as_json, inject_request, templated


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
        view_func = as_json(inject_request(view_func))
        return super(APIBlueprint, self).add_url_rule(rule, endpoint, view_func, **options)


class TemplateBlueprint(Blueprint):
    """Blueprint which automatically load and render template from templates directory
    """
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        # wrap with template loader function
        tpl_func = templated('/'.join([self.name, view_func.__name__]))
        view_func = tpl_func(view_func)
        # endpoint = options.pop("endpoint", view_func.__name__)
        return super(TemplateBlueprint, self).add_url_rule(rule, endpoint, view_func, **options)
