#!/usr/bin/env python
#-*- coding: utf-8 -*-
__author__ = 'francis'


class MethodRewriteMiddleware(object):
    def __init__(self, app, method_name='_method'):
        self.app = app
        self.name = method_name

    def __call__(self, environ, start_response):
        from werkzeug.urls import url_decode

        if self.name in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get(self.name).upper()
            req_method = environ['REQUEST_METHOD']
            if req_method == 'POST' and method in ['POST', 'PUT', 'DELETE']:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method

        return self.app(environ, start_response)
