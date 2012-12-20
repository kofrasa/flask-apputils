#!/usr/bin/env python

import json
import datetime as dt
from mongoalchemy.document import Document


def _mongo_serialize(value):
    if value is None or isinstance(value, (int,long,float,basestring,bool)):
        return value
    elif isinstance(value, (list,tuple,set)):
        return [_mongo_serialize(v) for v in value]
    elif isinstance(value, dict):
        for k,v in value.items():
            value[k] = _mongo_serialize(v)
        return value
    # change dates to isoformat
    elif isinstance(value, (dt.time, dt.date, dt.datetime)):
        value = value.replace(microsecond=0)
        return value.isoformat()
    elif isinstance(value, ActiveDocument):
        return value.to_dict()
    else:
        return str(value)


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
        
        for attr in filters:
            if attr not in doc_fields:
                continue

            value = filters[attr]
            if isinstance(value, tuple):
                # ensure only two values in tuple
                lower, upper = min(value), max(value)
                value = (lower,upper)
            elif not isinstance(value, (list,set)):
                value = [value]

            if len(value) == 1:
                # generate = statement
                criteria.append(getattr(self.cls,attr) == value[0])
            elif isinstance(value, tuple):
                # generate BETWEEN statement
                lower, upper = value            
                criteria.append(getattr(model,attr) >= value[0])
                criteria.append(getattr(model,attr) <= value[1])
            else:
                # generate IN statement
                criteria.append(getattr(model,attr).in_(value))
            
        self.filters.extend(criteria)
        return self

    def select(self, *fields):
        self.fields = list(fields) if len(fields) > 1 else [k.strip() for k in fields[0].split(',')]        
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

    def assign_attributes(self, **params):
        for attr in params:
            if attr in self._attr_protected: continue
            if attr in self._attr_accessible or not self._attr_accessible:
                if hasattr(self, attr):
                    setattr(self, attr, params[attr])

    def update_attributes(self, **params):
        self.assign_attributes(**params)
        self.save()
        return self


    def to_dict(self, *fields, **props):
        result = {}
        fields = list(fields)
        
        if fields and len(fields) == 1:
            fields = [s.strip() for s in fields[0].split(',')]
            
        fields = list(set(fields))
        if 'id' in fields:
            fields.remove('id')
            if 'mongo_id' not in fields:
                fields.append('mongo_id')        
        
        # pop of meta information
        meta = {}
        for k in ['_overwrite']:
            meta[k] = props.pop(k,None)
            
        # select columns specified, or all if none
        fields = fields or self.get_fields()
        for k in fields:
            if hasattr(self,k):
                v = _mongo_serialize(getattr(self, k))
                k = 'id' if k == 'mongo_id' else k
                result[k] = v

        # add extra properties
        for k in props:
            if meta['_overwrite'] or k not in result:
                result[k] = props[k]
                
        return result
    
    @classmethod
    def create(cls,**params):
        obj = cls(**params)
        obj.save()
        return obj

    @classmethod
    def find(cls,ident):
        return cls.query.get(ident)

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
