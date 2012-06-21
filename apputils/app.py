#-*- coding: utf-8 -*-

from flask.globals import g

def current_user():    
    """Gets the current user id from the request context"""
    return getattr(g.user,'id',None) if g and hasattr(g,'user') else None

    
def timestamp():
    """Gets the timestamp from the request context or current datetime"""
    import datetime as dt
    return g.timestamp if g and hasattr(g,'timestamp') else dt.datetime.utcnow()
    

def context_processor():
    """application context processor"""
    from flaskext.silk import send_silkicon
    from flaskext.htmlbuilder import html
    from .helpers import (
        render_template, static, get_flash, link_to, js_include_tag,
        css_link_tag, image_tag,
    )
    # rails style utility functions and more...
    return {
        'static': static,
        'silkicon': send_silkicon,
        'get_flash': get_flash,
        'link_to': link_to,
        'css_link_tag': css_link_tag,
        'js_include_tag': js_include_tag,
        'image_tag': image_tag,
        'html': html,
        'render': render_template,
    }
    
# convenience methods for accessing app.logger
def _log(level, msg, *args, **kwargs):
    from flask.globals import current_app as app
    log = {
        'debug': app.logger.debug,
        'error': app.logger.error,
        'info': app.logger.info,
        'warn': app.logger.warning
    }.get(level)(msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    _log('debug', msg, *args, **kwargs)
    

def warn(msg, *args, **kwargs):
    _log('warn', msg, *args, **kwargs)

    
def error(msg, *args, **kwargs):
    _log('error', msg, *args, **kwargs)
    

def info(msg, *args, **kwargs):
    _log('info', msg, *args, **kwargs)
    