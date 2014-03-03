#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import datetime as dt
from mongoalchemy.document import Document
from mongoalchemy.update_expression import UpdateExpression


def json_serialize(value):
    """Returns a JSON serializable python type of the given value
    
    :param value: A document or native type value
    """
    if value is None or isinstance(value, (int, long, float, basestring, bool)):
        return value
    elif isinstance(value, (list, tuple, set)):
        return [json_serialize(v) for v in value]
    elif isinstance(value, dict):
        for k, v in value.items():
            value[k] = json_serialize(v)
        return value
    # change dates to isoformat
    elif isinstance(value, (dt.time, dt.date, dt.datetime)):
        value = value.replace(microsecond=0)
        return value.isoformat()
    elif isinstance(value, Document):
        return _model_to_dict(value)
    else:
        return unicode(value)


def _model_to_dict(doc, *fields, **props):
    """Returns a JSON serializable `dict` representation of the given document(s)
    
    :param doc: mongo document or list of mongo documents
    :param \*fields: fields to select from the document
    :param \**props: extra properties to attach to JSON object
    """
    if not doc:
        return None

    result = []

    fields = list(fields)
    # handle aliases    
    alias = {'mongo_id': 'id'}
    temp_fields = fields[:]
    fields = []
    for k in temp_fields:
        if isinstance(k, tuple):
            alias[k[0]] = k[1]
            k = k[0]
        fields.append(k)

    # do this ONLY if fields are given
    if fields:
        fields.append('id')
        fields = set(fields) - set(['mongo_id'])

    # pop of meta information
    _overwrite = props.pop('_overwrite', None)
    _exclude = props.pop('_exclude', [])
    if isinstance(_exclude, basestring):
        _exclude = [e.strip() for e in _exclude.split(',')]

    many = not isinstance(doc, Document)
    if not many:
        doc = [doc]

    for d in doc:
        # select columns specified, or all if none
        fields = fields or d.get_fields()
        val = {}
        for k in fields:
            if k in _exclude:
                continue
            if hasattr(d, k):
                v = json_serialize(getattr(d, k))
                val[alias.get(k, k)] = v
        # add extra properties
        for k in props:
            val[k] = json_serialize(props[k])
        result.append(val)
    return result[0] if not many else result


class _QueryHelper(object):
    def __init__(self, cls):
        self.cls = cls
        self.fields = []
        self.filters = []

    @property
    def query(self):
        q = self.cls.query
        if self.fields:
            q = q.fields(*self.fields)
        if self.filters:
            q = q.filter(*self.filters)
        return q

    def all(self):
        return self.query.all()

    def first(self):
        return self.query.first()

    def one(self):
        return self.query.one()

    def where(self, *criteria, **filters):
        doc_fields = self.cls.get_fields()
        criteria = list(criteria) if criteria else []

        if 'id' in filters:
            filters['mongo_id'] = filters.pop('id')

        for attr in filters:
            if attr not in doc_fields or filters[attr] is None:
                continue

            value = filters[attr]
            if isinstance(value, tuple):
                # ensure only two values in tuple
                lower, upper = min(value), max(value)
                # generate BETWEEN statement         
                criteria.append(getattr(self.cls, attr) >= lower)
                criteria.append(getattr(self.cls, attr) <= upper)
            elif isinstance(value, (list, set)):
                # generate IN statement
                criteria.append(getattr(self.cls, attr).in_(*list(value)))
            else:
                # generate = statement
                criteria.append(getattr(self.cls, attr) == value)

        self.filters.extend(criteria)
        return self

    def select(self, *fields):
        if fields:
            for w in fields:
                self.fields.extend([k.strip() for k in w.split(',')])
        return self


class ActiveDocument(object):
    """Provides an extended query to MongoAlchemy DocumentField object
    """

    #attributes protected from mass assignment
    _attr_protected = tuple()

    #attributes accessible through mass assignments
    _attr_accessible = tuple()

    def __repr__(self):
        return json.dumps(self.to_dict())

    def __delattr__(self, field):
        q = self.__class__.query.filter(self.__class__.mongo_id == self.mongo_id)
        ex = UpdateExpression(q)
        ex.unset(getattr(self.__class__, field))
        ex.execute()

    def assign_attributes(self, **params):
        doc_fields = self.get_fields()
        for attr in params:
            if params[attr] is None:
                continue
            if attr in self._attr_protected:
                continue
            if attr in self._attr_accessible or not self._attr_accessible:
                if attr in doc_fields:
                    setattr(self, attr, params[attr])

    def update_attributes(self, **params):
        self.assign_attributes(**params)
        self.save()
        return self

    def to_dict(self, *fields, **props):
        return _model_to_dict(self, *fields, **props)

    @classmethod
    def create(cls, **params):
        for k, v in params.items():
            if v is None:
                params.pop(k)
        obj = cls(**params)
        obj.save()
        return obj

    @classmethod
    def find(cls, ident):
        return cls.query.get(ident)

    @classmethod
    def select(cls, *fields):
        q = _QueryHelper(cls)
        return q.select(*fields)

    @classmethod
    def where(cls, *criteria, **filters):
        q = _QueryHelper(cls)
        return q.where(*criteria, **filters)
