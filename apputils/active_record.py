#!/usr/bin/env python

import json
import datetime as dt
from sqlalchemy.orm import ColumnProperty, RelationshipProperty, object_mapper, class_mapper, defer, lazyload


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
    return {c.key: c for c in _get_mapper(model).iterate_properties
            if isinstance(c, ColumnProperty)}


def _get_relations(model):
    return {c.key: c for c in _get_mapper(model).iterate_properties
            if isinstance(c, RelationshipProperty)}


def _model_to_dict(models, *fields, **props):
    """Converts an SQL model object to JSON dict
    """
    result = []
    fields = list(fields)
    is_many = isinstance(models, list)
    if not is_many:
        models = [models]

    if fields and len(fields) == 1:
        fields = [s.strip() for s in fields[0].split(',')]

    # pop of meta information
    # _overwrite = props.pop('_overwrite', None)
    _exclude = props.pop('_exclude', [])
    if isinstance(_exclude, basestring):
        _exclude = [e.strip() for e in _exclude.split(',')]

    # select columns given or all if non was specified
    model_attr = set(_get_columns(models[0]))
    if fields:
        model_attr = model_attr & set(fields)
    else:
        fields = model_attr
    model_attr = model_attr - set(_exclude)

    related_attr = set(fields) - model_attr
    # check if there are relationships
    related_fields = _get_relations(models[0]).keys()
    related_map = {}
    # check if remaining fields are valid related attributes
    for k in related_attr:
        if '.' in k:
            index = k.index(".")
            model, attr = k[:index], k[index + 1:]
            if model in related_fields:
                related_map[model] = related_map.get(model, [])
            related_map[model].append(attr)
        elif k in related_fields:
            related_map[k] = []

    # no fields to return
    if not model_attr and not related_map:
        return {}

    for model in models:
        data = {}
        # handle column attributes
        for k in model_attr:
            if k in getattr(model, '_attr_hidden', []):
                continue
            v = getattr(model, k)
            # change dates to human readable format
            data[k] = json_serialize(v)

        # handle relationships
        for k in related_map:
            val = getattr(model, k)
            fields = related_map[k]
            data[k] = _model_to_dict(val, *fields)

            # add extra properties
        for k in props.keys():
            if k not in data:
                data[k] = props[k]

        # add to results
        result.append(data)

    # get correct response
    result = result if is_many else result[0]
    return result


def json_serialize(value):
    """Returns a JSON serializable python type of the given value
    
    :param value:
    """
    if value is None or isinstance(value, (int, long, float, basestring, bool)):
        return value
    elif isinstance(value, (list, tuple, set)):
        return [json_serialize(v) for v in value]
    elif isinstance(value, dict):
        for k, v in value.items():
            value[k] = json_serialize(v)
        return value
    # change dates to iso format
    elif isinstance(value, (dt.time, dt.date, dt.datetime)):
        value = value.replace(microsecond=0)
        return value.isoformat()
    elif isinstance(value, ActiveRecordMixin):
        return _model_to_dict(value)
    else:
        return unicode(value)


def _select(model, *fields):
    pk_columns = _primary_key_names(model)
    all_columns = _get_columns(model).keys()
    relations = _get_relations(model).keys()

    fields = list(set(fields)) if fields else all_columns

    # select all column properties if none is specified
    for attr in fields:
        if attr in all_columns:
            break
    else:
        fields.extend(all_columns)

    options = []

    # ensure PKs are included and defer unrequested attributes (including related)
    # NB: we intentionally allows fields like "related.attribute" to pass through

    for attr in (c.key for c in _get_mapper(model).iterate_properties):
        if attr not in fields:
            if attr in pk_columns:
                fields.append(attr)
            elif attr in all_columns:
                options.append(defer(attr))
            # relationships
            elif attr in relations:
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
    def _convert_dt(date_values, format_string):
        results = []
        for val in date_values:
            if isinstance(value, basestring):
                results.append(dt.datetime.strptime(val, format_string))
            else:
                results.append(val)
        return tuple(results) if isinstance(date_values, tuple) else results

    # build criteria from filter
    if filters:

        filter_keys = filters.keys()

        # select valid filters only
        columns = {c.name: c for c in _get_mapper(model).columns
                   if c.name in filter_keys}
        relations = {c.key: c for c in _get_mapper(model).iterate_properties
                     if isinstance(c, RelationshipProperty) and c.key in filter_keys}

        for attr, rel in relations.items():
            value = filters[attr]
            if not isinstance(value, list):
                value = [value]
                # validate type of object
            for v in value:
                assert not v or isinstance(v, rel.mapper.class_), "Type mismatch"

            if len(value) == 1:
                conditions.append(getattr(model, attr) == value[0])
            else:
                # Not implemented yet as of SQLAlchemy 0.7.9
                conditions.append(getattr(model, attr).in_(value))

        for attr, prop in columns.items():
            value = filters[attr]

            if isinstance(value, tuple):
                # ensure only two values in tuple
                lower, upper = min(value), max(value)
                value = (lower, upper)
            elif not isinstance(value, list):
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
                value = getattr(model, attr) == value.pop()
            elif isinstance(value, tuple):
                # generate BETWEEN statement
                lower = min(value)
                upper = max(value)
                value = getattr(model, attr).between(lower, upper)
            else:
                # generate IN statement
                value = getattr(model, attr).in_(value)

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

    def _query(self):
        q = self.cls.query
        if self.options:
            q = q.options(*self.options)
        if self.filters:
            q = q.filter(*self.filters)
        if self.order_by:
            q = q.order_by(*self.order_by)
        if self.group_by:
            q = q.group_by(*self.group_by)
            if self.having:
                q = q.having(self.having)
        return q

    def all(self):
        return self._query().all()

    def first(self):
        return self._query().first()

    def one(self):
        return self._query().one()

    def count(self):
        return self._query().count()

    def join(self, *props, **kwargs):
        return self._query().join(*props, **kwargs)

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
    _attr_protected = tuple()
    #attributes accessible through mass assignments and also returned by to_json
    _attr_accessible = tuple()
    # attributes protected from JSON serialization
    _attr_hidden = tuple()

    def __repr__(self):
        return json.dumps(self.to_dict())

    def assign_attributes(self, **params):
        for attr in params:
            if attr in self._attr_protected:
                continue
            if not self._attr_accessible or attr in self._attr_accessible:
                if hasattr(self, attr):
                    setattr(self, attr, params[attr])
        return self

    def update_attributes(self, **params):
        self.assign_attributes(**params)
        return self.save(commit=True)

    def save(self, commit=False):
        self.query.session.add(self)
        if commit:
            self.query.session.commit()
        return self

    def delete(self, commit=False):
        self.query.session.delete(self)
        if commit:
            self.query.session.commit()
        return self

    def to_dict(self, *fields, **props):
        return _model_to_dict(self, *fields, **props)

    @classmethod
    def create(cls, **kw):
        return cls(**kw).save(commit=True)

    @classmethod
    def find(cls, ident):
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
        q.select(*fields)
        return q

    @classmethod
    def where(cls, *criteria, **filters):
        q = _QueryHelper(cls)
        q.where(*criteria, **filters)
        return q
