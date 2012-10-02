#!/usr/bin/env python

import datetime as dt
from flask_sqlalchemy import SQLAlchemy


class SQLAlchemyExt(SQLAlchemy):

    def commit(self):
        return self.session.commit()

    def rollback(self):
        return self.session.rollback()

    def execute(self, obj, *multiparams, **params):
        conn = self.engine.connect()
        result = conn.execute(obj, *multiparams, **params)
        return result

    def add(self, model):
        self.session.add(model)

    def remove(self):
        self.session.remove()

    def query(self, *args, **kwargs):
        return self.session.query(*args, **kwargs)


from sqlalchemy.orm import ColumnProperty, RelationshipProperty \
                            , object_mapper, class_mapper


def _get_mapper(obj):
    """Returns the primary mapper for the given instance or class"""
    its_a_model = isinstance(obj, type)
    mapper = class_mapper if its_a_model else object_mapper
    return mapper(obj)

def _primary_key_names(obj):
    """Returns the name of the primary key of the specified model or instance
    of a model, as a string.

    If `model_or_instance` specifies multiple primary keys and ``'id'`` is one
    of them, ``'id'`` is returned. If `model_or_instance` specifies multiple
    primary keys and ``'id'`` is not one of them, only the name of the first
    one in the list of primary keys is returned.
    """
    return [key.name for key in _get_mapper(obj).primary_key]


def _get_columns(model):
    """Returns a dictionary-like object containing all the columns properties of the
    specified `model` class.
    """
    return {c.key:c for c in _get_mapper(model).iterate_properties
                if isinstance(c, ColumnProperty)}


def _get_relations(model):
    return {c.key:c for c in _get_mapper(model).iterate_properties
                if isinstance(c, RelationshipProperty)}


def _select(model, *fields):

    from sqlalchemy.orm import defer, lazyload

    PK_COLUMNS = _primary_key_names(model)
    COLUMNS = _get_columns(model).keys()
    RELATIONS = _get_relations(model).keys()

    fields = list(set(fields)) if fields else COLUMNS

    # select all column properties if none is specified
    for attr in fields:
        if attr in COLUMNS:
            break
    else:
        fields.extend(COLUMNS)

    options = []
    # ensure PKs are included and defer unrequested attributes (includes related)
    for attr in (c.key for c in _get_mapper(model).iterate_properties):
        if attr not in fields:
            if attr in PK_COLUMNS:
                fields.append(attr)
            elif attr in COLUMNS:
                options.append(defer(attr))
            # relationships
            elif attr in RELATIONS:
                options.append(lazyload(attr))
    return options


def _where(model, *criteria, **filters):
    """Builds a list of where conditions for this applying the correct operators
    for representing the values.

    `=` expression is generated for single simple values (int, str, datetime, etc.)
    `IN` expression is generated for list/set of simple values
    `BETWEEN` expression is generated for 2-tuple of simple values
    """
    conditions = []
    conditions.extend(criteria)

    # converts a date/time string to the corresponding python object
    def _convert_dt(val, format_string):
        tmp = val
        val = []
        for v in tmp:
            if isinstance(v,basestring):
                val.append(dt.datetime.strptime(v, format_string))
        return tuple(val) if isinstance(tmp, tuple) else val
    # build criteria from filters
    if filters:
        columns = {c.name:c for c in _get_mapper(model).columns
                    if c.name in filters.keys()}

        for attr in columns:
            value = filters[attr]
            prop = columns[attr]

            if isinstance(value, tuple):
                # ensure only two values in tuple
                lower, upper = min(value), max(value)
                value = (lower,upper)
            elif not isinstance(value, (list,set)):
                value = [value]

            # format expression for datetime values
            if prop.type.python_type == dt.datetime:
                value = _convert_dt(value, "%Y-%m-%d %H:%M:%S")
            elif prop.type.python_type == dt.date:
                value = _convert_dt(value, "%Y-%m-%d")
            elif prop.type.python_type == dt.time:
                value = _convert_dt(value, "%H:%M:%S")

            if len(value) == 1:
                # generate = statement
                value = getattr(model,attr) == value.pop()
            elif isinstance(value, tuple):
                # generate BETWEEN statement
                lower = min(value)
                upper = max(value)
                value = getattr(model,attr).between(lower,upper)
            else:
                # generate IN statement
                value = getattr(model,attr).in_(value)

            conditions.append(value)
    return conditions


class _QueryHelper(object):

    def __init__(self, model):
        self.cls = model
        self.options = []
        self.filters = []
        self.order_by = []
        self.group_by = []
        self.having = None

    def query(self):
        q = self.cls.query
        if self.options:
            q.options(*self.options)
        if self.filters:
            q.filter(*self.filters)
        if self.order_by:
            q.order_by(*self.order_by)
        if self.group_by:
            q.group_by(*self.group_by)
            if self.having:
                q.having(self.having)
        return q

    def all(self):
        return self.query().all()

    def first(self):
        return self.query().first()

    def one(self):
        return self.query().one()

    def where(self, *criteria, **filters):
        conditions = _where(self.cls, *criteria, **filters)
        self.filters.extend(conditions)
        return self

    def select(self, *fields):
        options = _select(self.cls, *fields)
        self.options.extend(options)
        return self

    def order_by(self, *criteria):
        self.order_by.extend(criteria)
        return self

    def group_by(self, *criteria):
        self.group_by.extend(criteria)
        return self

    def having(self, criterion):
        self.having = criterion
        return self



class ActiveRecordMixin(object):
    """Provides an extended query function with some Rails style candy,
    for db.Model classes defined for SQLAlchemy.

    Example:

    class User(db.Model, ActiveRecordMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True)
        email = db.Column(db.String(120), unique=True)
        addresses = db.relationship('Address', backref='user',lazy='joined')

    class Address(db.Model, ActiveRecordMixin):
        id = db.Column(db.Integer, primary_key=True)
        city = db.Column(db.String(50))
        state = db.Column(db.String(50))
        street = db.Column(db.String(50))
        number = db.Column(db.Integer)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    """

    #attributes protected from mass assignment
    attr_protected = tuple()

    #attributes accessible through mass assignments and also returned by to_json
    attr_accessible = tuple()

    def __init__(self, **params):
        self.assign_attributes(**params)

    def assign_attributes(self, **params):
        for attr in params:
            if attr in self.attr_protected: continue
            if attr in self.attr_accessible or not self.attr_accessible:
                if hasattr(self, attr):
                    setattr(self, attr, params[attr])

    def update_attributes(self, **params):
        self.assign_attributes(**params)
        return self.save()

    def save(self):
        self.query.session.add(self)
        self.query.session.commit()
        return self

    def to_dict(self, include=None):
        result = {}
        for k in _get_columns(self):
            if not include or k in include:
                result[k] = getattr(self, k)
                # change dates to isoformat
                if isinstance(result[k], (dt.time, dt.date, dt.datetime)):
                    result[k] = result[k].isoformat()
        # handle relationships
        for k, rel in _get_relations(self).items():
            if not include or k in include:
                relcolumns = _get_columns(rel.mapper.class_)
                for c in (r.key for r in rel.remote_side):
                    relcolumns.pop(c)
                value = getattr(self, k)
                if isinstance(value, list):
                    result[k] = [val.to_dict(include=relcolumns.keys())
                                 for val in value]
                else:
                    result[k] = value.to_dict(include=relcolumns.keys())
        return result

    @classmethod
    def find(cls,ident):
        return cls.query.get(ident)

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def first(cls):
        return cls.query.first()

    @classmethod
    def select(cls, *fields):
        q = _QueryHelper(cls)
        q.select(cls,*fields)
        return q

    @classmethod
    def where(cls, *criteria, **filters):
        q = _QueryHelper(cls)
        q.where(*criteria, **filters)
        return q
