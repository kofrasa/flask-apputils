#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import datetime as dt
from mongoalchemy.document import Document


def _mongo_serialize(value):
    """Serializes mongo values
    """
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
    

def _mongo_dict(doc,*fields,**props):
    """Returns a JSON serializable representation of the given document(s)
    """
    if not doc:
        return None
    
    result = []
    fields = list(fields)
    
    if fields and len(fields) == 1:
        fields = [s.strip() for s in fields[0].split(',')]
        
    fields = list(set(fields))
    if 'id' in fields:
        fields.remove('id')
        if 'mongo_id' not in fields:
            fields.append('mongo_id')        
    
    # pop of meta information
    _overwrite = props.pop('_overwrite', None)
    _exclude = props.pop('_exclude', [])
    if isinstance(_exclude,basestring):
        _exclude = [e.strip() for e in _exclude.split(',')]
    
    many = not isinstance(doc, ActiveDocument)
    if not many:
        doc = [doc]
        
    for d in doc:
        # select columns specified, or all if none
        fields = fields or d.get_fields()
        val = {}
        for k in fields:
            if k in _exclude: continue
            if hasattr(d,k):
                v = _mongo_serialize(getattr(d, k))
                k = 'id' if k == 'mongo_id' else k
                val[k] = v
    
        # add extra properties
        for k in props:
            if _overwrite or k not in val:
                val[k] = props[k]
        
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
                criteria.append(getattr(self.cls,attr) >= lower)
                criteria.append(getattr(self.cls,attr) <= upper)
            elif isinstance(value, (list,set)):
                # generate IN statement
                criteria.append(getattr(self.cls,attr).in_(*list(value)))
            else:
                # generate = statement
                criteria.append(getattr(self.cls,attr) == value)
            
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

    def assign_attributes(self, **params):
        for attr in params:
            if params[attr] is None: continue
            if attr in self._attr_protected: continue
            if attr in self._attr_accessible or not self._attr_accessible:
                if hasattr(self,attr):
                    setattr(self, attr, params[attr])

    def update_attributes(self, **params):
        self.assign_attributes(**params)
        self.save()
        return self

    def to_dict(self, *fields, **props):
        return _mongo_dict(self,*fields,**props)
    
    @classmethod
    def create(cls,**params):
        for k,v in params.items():
            if v is None:
                params.pop(k)
        obj = cls(**params)
        obj.save()
        return obj

    @classmethod
    def find(cls,ident):
        return cls.query.get(ident)

    @classmethod
    def select(cls, *fields):
        q = _QueryHelper(cls)
        return q.select(*fields)

    @classmethod
    def where(cls, *criteria, **filters):
        q = _QueryHelper(cls)
        return q.where(*criteria, **filters)
