#!/usr/bin/env python

# data validation routines borrowed from wtforms.

EMAIL_PATTERN = "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"
PHONE_PATTERN = "^[0-9]{10,15}$"

class ValidationError(ValueError):
    """
    Raised when a validator fails to validate its input.
    """
    def __init__(self, message=u'', *args, **kwargs):
        ValueError.__init__(self, message, *args, **kwargs)


def email(value):
    return regexp(EMAIL_PATTERN, u"Invalid email address")(value)


def phone(value):
    return regexp(PHONE_PATTERN, u"Invalid phone number")(value)


def length(min=-1, max=-1, message=None):
    assert min != -1 or max!=-1, 'At least one of `min` or `max` must be specified.'
    assert max == -1 or min <= max, '`min` cannot be more than `max`.'
    def wrapper(data):
        l = data and len(data) or 0
        if l < min or max != -1 and l > self.max:
            if message is None:
                if max == -1:
                    message = u'Field must be at least %(min)d character long.' % min
                elif min == -1:
                    message = u'Field cannot be longer than %(max)d character.' % max
                else:
                    self.message = u'Field must be between %(min)d and %(max)d characters long.'

            raise ValidationError(message % dict(min=min, max=max))
        return data
    return wrapper


def any_of(values, message=None):
    def wrapper(data):
        if data not in values:
            if message is None:
                message = u"Invalid value, must be one of: %s." % str(values)
            raise ValueError(message)
        return data
    return wrapper


def none_of(values, message=None):
    def wrapper(data):
        if data in values:
            if message is None:
                message = u"Invalid value, can't be any of: %s." % str(values)
            raise ValueError(message)
        return data
    return wrapper


def required(message=None):
    def wrapper(data):
        if not data or isinstance(data, basestring) and not data.strip():
            if message is None:
                message = u'This value is required.'
            raise ValueError(message)
        return data
    return wrapper


def equals(value,message=None):
    def wrapper(data):
        if data != value:
            if message is None:
                message = u'Value must be equal to %s.' % str(value)
            raise ValidationError(message)
        return data
    return wrapper


def range(min=None, max=None, message=None):
    """
    Validates that a number is of a minimum and/or maximum value, inclusive.
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
    def wrapper(data):
        if data is None or (min is not None and data < min) or \
            (max is not None and data > max):
            if message is None:
                # we use %(min)s interpolation to support floats, None, and
                # Decimals without throwing a formatting exception.
                if max is None:
                    message = u'Number must be greater than %s.' % min
                elif min is None:
                    message = u'Number must be less than %s.' % max
                else:
                    message = u'Number must be between %s and %s.' % (min, max)
            raise ValidationError(message)
        return data
    return wrapper


def regexp(pattern,message):
    def wrapper(data):
        import re
        if not re.match(pattern, data or u''):
            if message is None:
                message = u'Invalid Input.'
            raise ValidationError(message)
        return data
    return wrapper