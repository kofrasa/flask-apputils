#!/usr/bin/env python

import json
from functools import wraps
from flask import request, redirect, jsonify, Response, render_template, url_for


def after_this_request(f):
    """Decorator for functions to run after request has been processed"""
    from flask import g
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


def with_template(*template):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            template_name = '/'.join(template)
            if template_name is None:
                # get template from templates directory
                template_name = request.endpoint.replace('.', '/')
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name + '.html', **ctx)
        return wrapper
    return decorator


def inject_request_params(f):
    """
    A decorator to inject request data into the handler as parameters.
    For GET requests, the query parameters are injected.
    For POST,PUT and PATCH requests the following occurs.
    If the request is a form submission the form data is injected otherwise, the request body is
    parsed as JSON and injected

    :param f: the request handler
    :return:
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask.globals import request
        data = {}
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.form:
                data = dict(request.form.items())
            else:
                try:
                    data = json.loads(request.data)
                except Exception:
                    pass
        else:
            data = {}
            for key in request.args:
                data[key] = request.args.get(key)

        kwargs.update(data)
        return f(*args, **kwargs)
    return wrapper


def validate(fn, endpoint=None, url=None):
    """
    Returns a decorator which executes the given validator function before running the handler.
    The validator must raise an `Exception` if it fails.
    :param fn: the validator function
    :param url: a redirect url to send the user to when validation fails
    :return:
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                fn()
                return f(*args, **kwargs)
            except Exception:
                if endpoint:
                    return redirect(url_for(endpoint))
                return redirect(url)
        return wrapper
    return decorator


def inject_response(extra):
    """
    Injects extra data into the response of the request handler
    This works only if the response is a dictionary. Useful for JSON APIs
    :param extra:
    :return: `function` a decorator function
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
    """
    Validates whether the request should come over SSL.
    Set the SSL config parameter to `True`
    :param f:
    :return:
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
    """
    A decorator to return the `dict` response as JSON to the caller
    :param f:
    :return:
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        if isinstance(res, Response):
            return res
        elif isinstance(res, dict):
            return jsonify(**res)
        else:
            return jsonify(data=res)
    return wrapper


def cached(app, timeout=5 * 60, key='view/%s'):
    """http://flask.pocoo.org/docs/patterns/viewdecorators/#caching-decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = key % request.path
            rv = app.cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            app.cache.set(cache_key, rv, timeout=timeout)
            return rv
        return wrapper
    return decorator