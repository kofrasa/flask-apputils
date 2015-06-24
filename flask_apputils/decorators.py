# -*- coding: utf-8 -*-
"""
    flask_apputils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Useful decorators to enhance route handlers
"""

from functools import wraps
from flask import request, redirect, Response, render_template, jsonify
from .helpers import json_value

__all__ = (
    'after_this_request',
    'as_json',
    'ssl_required',
    'with_request_body',
    'with_request_params',
    'with_template'
)


def after_this_request(f):
    """Decorator for functions to run after request has been processed"""
    from flask import g

    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


def with_template(template=None, render_func=render_template):
    """Render a template using the `dict` result of the function as context.

    The function result is returned as is when not a `dict`.
    If not template name is given, a formatted endpoint name is used by
    replacing '.' with the path separator

    See: example_

    .. example: http://flask.pocoo.org/docs/0.10/patterns/viewdecorators/#templating-decorator
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint.replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_func(template_name, **ctx)

        return wrapper

    return decorator


def with_request_params(f):
    """Inject request query parameters into the function as \**kwargs

    :param f: function
    :return:
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        data = {}
        for key in request.args:
            data[key] = request.args.get(key)
        if data:
            kwargs.update(data)
        return f(*args, **kwargs)

    return wrapper


def with_request_body(f):
    """Inject request body into the function as \**kwargs for methods POST, PUT, or PATCH.

    If the content-type is JSON, the body will be treated as JSON, otherwise as a form-data.

    :param f: function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                data = request.get_json()
                if data is None:
                    data = dict(request.form.items())

                if isinstance(data, dict):
                    kwargs.update(data)
            except Exception as e:
                print e

        return f(*args, **kwargs)

    return wrapper


def ssl_required(f):
    """Force requests to be secured with SSL. Must set the `SSL` config parameter to `True`

    :param f: function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import current_app as app

        if app.config.get("SSL"):
            if request.is_secure:
                return f(*args, **kwargs)
            else:
                return redirect(request.url.replace("http://", "https://"))
        return f(*args, **kwargs)

    return wrapper


def as_json(f):
    """Return result as a JSON response.

    Responses of type :class:`flask.wrappers.Response` are returned as is.
    Responses of type :class:`dict` are serialized to JSON.
    All other response types are serialized to JSON and returned
    in an object with key `result` such as: {'result': True}

    :param f: function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        response = f(*args, **kwargs)
        if response is None:
            raise Exception("Cannot serialize None to JSON")
        if isinstance(response, Response):
            return response
        if not callable(response):
            response = json_value(response)
        if isinstance(response, dict):
            return jsonify(**response)
        else:
            return jsonify(result=response)

    return wrapper
