#!/usr/bin/env python

import json
from functools import wraps

def after_this_request(f):
    """Decorator for functions to run after request has been processed"""
    from flask import g
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


def templated(template=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from .helpers import render_template   
            template_name = template
            if template_name is None:
                template_name = request.endpoint.replace('.', '/')
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return wrapper
    return decorator


def ssl_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request, redirect, current_app as app
        if app.config.get("SSL"):
            if request.is_secure:
                return f(*args, **kwargs)
            else:
                return redirect(request.url.replace("http://", "https://"))        
        return f(*args, **kwargs)            
    return wrapper


def as_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import jsonify
        from flask.wrappers import Response
        res = f(*args, **kwargs)
        if isinstance(res, Response):
            return res        
        return jsonify(res)
    return wrapper


def cached(app, timeout=5 * 60, key='view/%s'):
    '''http://flask.pocoo.org/docs/patterns/viewdecorators/#caching-decorator'''
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import current_app as app
            cache_key = key % request.path
            rv = app.cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            app.cache.set(cache_key, rv, timeout=timeout)
            return rv
        return wrapper
    return decorator