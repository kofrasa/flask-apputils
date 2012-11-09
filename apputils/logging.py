#!/usr/bin/env python

# convenience methods for accessing app.logger
from flask.globals import current_app as app

def _get_logger(level):
    def logger(msg, *args, **kwargs):
        fn = getattr(app.logger, level)
        fn(msg, *args, **kwargs)
    return logger

debug = _get_logger('debug')
error = _get_logger('error')
warn = _get_logger('warning')
info = _get_logger('info')
