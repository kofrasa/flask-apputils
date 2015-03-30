# -*- coding: utf-8 -*-
"""
    flask_apputils.helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""

import collections
from datetime import datetime, date, time


def json_value(value):
    """Convert any `python` object to a JSON primitive value.
    To support any arbitrary object, implement `to_json` method
    which is used to convert a `python` object types to a JSON primitive.

    :param value: the `python` object to return as a valid JSON primitive
    """
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    elif isinstance(value, collections.Iterable):
        return [json_value(v) for v in value]
    elif isinstance(value, dict):
        for k, v in value.items():
            value[k] = json_value(v)
        return value
    elif isinstance(value, (datetime, date, time)):
        if isinstance(value, (datetime, time)):
            value = value.replace(microsecond=0)
        return value.isoformat()
    elif hasattr(value, 'to_json') and callable(getattr(value, 'to_json')):
        return json_value(value.to_dict())
    else:
        return str(value)
