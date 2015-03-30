# -*- coding: utf-8 -*-
"""
    flask_apputils.filters
    ~~~~~~~~~~~~~~~~~~~~~~
"""

import datetime as dt
import math


def moment(value):
    delta = dt.datetime.now() - value
    if delta.days == 0:
        formatting = 'today'
    elif delta.days < 10:
        formatting = '{0} days ago'.format(delta.days)
    elif delta.days < 28:
        formatting = '{0} weeks ago'.format(int(math.ceil(delta.days/7.0)))
    elif value.year == dt.datetime.now().year:
        formatting = 'on %d %b'
    else:
        formatting = 'on %d %b %Y'
    return value.strftime(formatting)