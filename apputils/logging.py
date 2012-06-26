#!/usr/bin/env python

# convenience methods for accessing app.logger

from flask.globals import current_app as app

def _create_logger(fn):    
    def logger(msg, *args, **kwargs):        
        fn(msg, *args, **kwargs)
    return logger

debug = _create_logger(app.logger.debug)
error = _create_logger(app.logger.error)
warn = _create_logger(app.logger.warning)
info = _create_logger(app.logger.info)