#!/usr/bin/env python

import re

EMAIL_PATTERN = "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"


class ValidationError(ValueError):
    """
    Raised when a validator fails to validate its input.
    """
    def __init__(self, message='', *args, **kwargs):
        ValueError.__init__(self, message, *args, **kwargs)


def email(value):
    return regexp(value, EMAIL_PATTERN)("Invalid email address")


def length(value, min=1, max=None):
    assert min or max, 'No bounds specified'
    assert (not max or min <= max) or \
        (not max or max > 0) and min > 0, "Invalid bounds specified"

    def wrapper(message=None):
        if value is not None:
            assert isinstance(value, basestring), "Invalid value type"
            size = len(str(value))
            if min is not None and size < min:
                message = message or "Must be greater than %(min)s characters"
            elif max is not None and size > max:
                message = message or "Must be less than %(max)s characters"
            else:
                message = message or "Must be between %(min)s and %(max)s characters"
            raise ValidationError(message % dict(min=min,max=max))
        return value
    return wrapper


def any_of(value, options):
    def wrapper(message=None):
        if value is not None and value not in options:
            if message is None:
                message = "Must be any of: %r." % value
            raise ValueError(message)
        return value
    return wrapper


def none_of(value, options):
    def wrapper(message=None):
        if value is not None and value in options:
            if message is None:
                message = "Cannot be any of: %r" % value
            raise ValueError(message)
        return value
    return wrapper


def required(value):
    def wrapper(message='Required'):
        if not value or isinstance(value, basestring) and not value.strip():
            raise ValueError(message)
        return value
    return wrapper


def equals(value, expected):
    def wrapper(message):
        if value != expected:
            if message is None:
                message = 'Must be equal to %s' % value
            raise ValidationError(message)
        return value
    return wrapper


def range(value, min=None, max=None):
    """
    Validates that a number is within a minimum and/or maximum value, inclusive.
    This will work with any comparable number type, such as floats and
    decimals, not just integers.

    :param min:
        The minimum required value of the number. If not provided, minimum
        value will not be checked.
    :param max:
        The maximum value of the number. If not provided, maximum value
        will not be checked.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated using `%(min)s` and `%(max)s` if desired. Useful defaults
        are provided depending on the existence of min and max.
    """
    assert min or max, "Invalid bounds specified"

    def wrapper(message=None):
        if value is not None:
            if min is not None and value < min:
                message = message or "Must be greater than %(min)s"
            elif max is not None and value > max:
                message = message or "Must be less than %(max)s"
            else:
                message = message or "Must be between %(min)s and %(max)s"
            raise ValidationError(message % dict(min=min,max=max))
        return value
    return wrapper


def regexp(value, pattern):
    def wrapper(message="Invalid format"):
        if value and not re.match(pattern, value):
            raise ValidationError(message)
        return value
    return wrapper