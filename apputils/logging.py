#!/usr/bin/env python


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