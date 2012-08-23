# -*- coding: utf-8 -*-

import os
from functools import wraps
from flask import g, url_for, get_flashed_messages
from flask.helpers import send_file
from flaskext.mako import render_template as render
from flaskext.htmlbuilder import html

__all__ = [
    'static',
    'render_template',
    'load_template'
    'get_flash',
    'image_tag',
    'js_include_tag',
    'css_link_tag',
    'link_to',
]


def static(filename):
    return url_for('static', filename=filename)


def render_template(filename, **context):
    from flask.globals import current_app as app
    
    context = context or {}    
    app.update_template_context(context)

    # flask-mako already injects: g, request, and session
    for k in ('g','request','session'):
        context.pop(k, None)
    filename += '.html' if '.' not in filename else ''
    return render(filename, **context)


def load_template(filename, **context):
    template = render_template(filename, **context)
    name = str(os.path.splitext(filename)[0]).replace(os.path.sep, '_')
    return unicode(
        html.script(id=name, type='text/html')(html.safe(template))
    )


def get_flash(category=None, sep='\n'):
    if not category:
        return sep.join(get_flashed_messages())
    messages = get_flashed_messages(with_categories=True)
    return sep.join([m for k,m in messages if k == category])

    
def link_to(text, endpoint, **kwargs):
    try:
        url = url_for(endpoint)
        endpoint = url
    except:
        pass
    return unicode(html.a(href=endpoint, **kwargs)(text))
    
    
def css_link_tag(filename, **kwargs):
    from flask.globals import current_app as app
    
    try:
        filepath = 'css/' +  filename + '.css'
        rel = 'stylesheet'
        path = static(filepath)        
        fp = app.send_static_file(filepath)
        fp.close()
    except:
        path = static('css/' +  filename + '.less')
        rel = 'stylesheet/less'

        
    for k in ('rel','type','href'):
        kwargs.pop(k,None)
        
    return unicode(html.link(rel=rel, type="text/css", href=path, **kwargs))

    
def js_include_tag(filename, **kwargs):
    return unicode(html.script(type="text/javascript",
                               src=static('js/'+filename+'.js'), **kwargs)())

    
def image_tag(filename, **kwargs):
    return unicode(html.img(src=static('img/' + filename), **kwargs))
    
    
def format_html(template):
    def inner(**context):
        template_name = template
        if template_name is None:
            template_name = request.endpoint.replace('.', '/')
        return render_template(template_name, **context)
    return inner
