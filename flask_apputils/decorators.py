# -*- coding: utf-8 -*-
"""
    flask_apputils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Collection of useful decorator patterns.
"""

import json
from functools import wraps
from flask import request, redirect, Response, render_template, jsonify
from werkzeug.exceptions import NotFound
from .helpers import json_value


def after_this_request(f):
    """Decorator for functions to run after request has been processed"""
    from flask import g

    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


def templated(template=None):
    """Load template and process with argument `dict` returned from handler.
    Will use a formatted endpoint name as template name if not provided.

    See: http://flask.pocoo.org/docs/0.10/patterns/viewdecorators/#templating-decorator
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
            return render_template(template_name, **ctx)

        return wrapper

    return decorator


def inject_request(f):
    """Injects request data into the wrapped handler as **kwargs parameters.

    For `GET` requests, the query parameters are injected.

    For all HTTP request methods, form data is injected if using multipart/form-data else
    the request body is assumed to be JSON and is deserialized and injected.

    :param f: request handler
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        query = {}
        for key in request.args:
            query[key] = request.args.get(key)

        if request.method in ['GET']:
            data = query
        else:
            try:
                data = json.loads(request.data)
                assert isinstance(data, dict)
            except Exception as e:
                data = dict(request.form.items())

        if isinstance(data, dict):
            kwargs.update(data)

        return f(*args, **kwargs)

    return wrapper


def inject_response(extra):
    """Injects extra data into the response of the request handler

    This works only if the response is a dictionary and is suitable for JSON APIs

    :param extra:
    :return: a decorator function
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            res = f(*args, **kwargs)
            if res is None:
                res = dict()
            if isinstance(res, dict) and not set(extra.keys()) & set(res.keys()):
                for key, value in extra.items():
                    if callable(value):
                        res[key] = value()
                    else:
                        res[key] = value
            return res

        return wrapper

    return decorator


def ssl_required(f):
    """Force requests to be secured with SSL.
    Must set the `USE_SSL` config parameter to `True`

    :param f: request handler
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import current_app as app

        if app.config.get("USE_SSL"):
            if request.is_secure:
                return f(*args, **kwargs)
            else:
                return redirect(request.url.replace("http://", "https://"))
        return f(*args, **kwargs)

    return wrapper


def as_json(f):
    """Serialize a response to JSON

    :param f: request handler
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        response = f(*args, **kwargs)
        if response is None:
            raise NotFound()
        if isinstance(response, Response):
            return response
        if not callable(response):
            response = json_value(response)
        if isinstance(dict, response):
            return jsonify(**response)
        else:
            return jsonify(data=response)

    return wrapper