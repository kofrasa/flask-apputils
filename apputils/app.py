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