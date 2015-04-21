# -*- coding: utf-8 -*-
"""
    flask_apputils.helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""

from datetime import datetime, date, time


def json_value(value):
    """Convert a object to a JSON primitive value

    To support any arbitrary object, implement `to_json` or `to_dict`
    method on the object t return a valid JSON primitive

    :param value: the value to convert to a JSON primitive
    """
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    elif isinstance(value, (list, set, tuple)):
        return [json_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: json_value(value[k]) for k in value}
    elif isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
        return json_value(value.to_dict())
    elif hasattr(value, 'to_json') and callable(getattr(value, 'to_json')):
        return json_value(value.to_json())
    else:
        return str(value)
