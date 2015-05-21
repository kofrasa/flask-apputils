# -*- coding: utf-8 -*-
"""
    flask_apputils.routing
    ~~~~~~~~~~~~~~~~~~~~~~

    Utilities for building route handlers
"""

from werkzeug.utils import import_string, cached_property
from flask.blueprints import Blueprint
from .decorators import as_json, inject_request_body, templated


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
    """
    Create a router function that lazily load and dispatch routes.

    :param blueprint: the app or blueprint
    :param module_name: the full module name to use for registered handlers
    :return:
    """
    names = []

    def router(url_rule, func_name, **options):
        """
        Register route urls and handlers

        :param url_rule: route url rule
        :param func_name: handler function
        :param options: route options
        :return:
        """
        view = LazyView(module_name + "." + func_name)
        # generate endpoint to handle multiple import names
        # this necessary to allow clean looking urls (no trailing slash)
        names.append(func_name)
        if func_name in names:
            endpoint = func_name + "_" + str(names.count(func_name))
        else:
            endpoint = func_name
        blueprint.add_url_rule(url_rule, endpoint, view_func=view, **options)

    return router


class APIBlueprint(Blueprint):
    """
    Blueprint which inject request body into handler return responses as JSON.
    """

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        view_func = as_json(inject_request_body(view_func))
        return super(APIBlueprint, self).add_url_rule(rule, endpoint, view_func, **options)


class TemplateBlueprint(Blueprint):
    """
    Blueprint which loads and render templates with response data as context
    """

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        tpl_func = templated('/'.join([self.name, view_func.__name__]))
        view_func = tpl_func(view_func)
        # endpoint = options.pop("endpoint", view_func.__name__)
        return super(TemplateBlueprint, self).add_url_rule(rule, endpoint, view_func, **options)
