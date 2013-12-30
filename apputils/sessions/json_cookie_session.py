#!/usr/bin/env python
#-*- coding: utf-8 -*-
__author__ = 'francis'


import json
from flask.sessions import SecureCookieSession, SecureCookieSessionInterface


class JSONCookieSession(SecureCookieSession):
    serialization_method = json


class JSONCookieSessionInterface(SecureCookieSessionInterface):
    session_class = JSONCookieSession