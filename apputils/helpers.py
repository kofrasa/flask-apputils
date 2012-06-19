# -*- coding: utf-8 -*-

from flask import g, url_for, get_flashed_messages
from flaskext.mako import render_template as render
from flaskext.htmlbuilder import html

__all__ = [
    'static',
    'render_template',
    'get_message',
    'get_image',
    'image_tag',
    'js_include_tag',
    'css_link_tag',
    'link_to',
]

def static(filename):
    return url_for('static', filename=filename)


def render_template(name, **context):
    from flask.globals import current_app as app
    
    context = context or {}    
    app.update_template_context(context)

    # flask-mako already injects: g, request, and session
    for k in ('g','request','session'):
        context.pop(k, None)
    name += '.html' if '.' not in name else ''
    return render(name, **context)


def get_flash(category=None):
    if not category:
        return '\n'.join(get_flashed_messages())
    messages = get_flashed_messages(with_categories=True)
    return '\n'.join([m for k,m in messages if k == category])
    
def link_to(text, endpoint, **kwargs):
    return unicode(html.a(href=url_for(endpoint), **kwargs)(text))
    
def css_link_tag(filename, **kw):
    ext = '.css' if filename[-5:] != '.less' else ''
    rel = "stylesheet" if ext else "stylesheet/less"
    path = static('css/' + filename + ext)
    
    for k in ('rel','type','href'):
        kw.pop(k,None)
        
    return unicode(html.link(rel=rel, type="text/css", href=path, **kw))
    
def js_include_tag(filename):
    return unicode(html.script(type="text/javascript",
                               src=static('js/'+filename+'.js'))())
    
def image_tag(filename, alt=''):
    return unicode(html.img(alt=alt, src=static('img/' + filename)))
