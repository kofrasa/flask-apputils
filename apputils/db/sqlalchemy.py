#!/usr/bin/env python

import datetime as dt
from flask_sqlalchemy import SQLAlchemy
from flask import abort


class _SQLAlchemyExt(SQLAlchemy):

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


db = _SQLAlchemyExt()

from sqlalchemy.orm import ColumnProperty, RelationshipProperty
from sqlalchemy.sql.expression import ClauseElement


def _get_pk(model):
    return [c.name for c in model.__table__.primary_key]

def _get_columns(model):
    return [c.name for c in model.__table__.columns]

def _get_custom(model):
    attribs = []
    s = len(model.__name__) + 1
    columns = _get_columns(model)
    for c in model.__mapper__.iterate_properties:
        if isinstance(c, ColumnProperty):
            name = str(c)[s:]
            if name not in columns:
                attribs.append(name)
    return attribs

def _get_relations(model):
    attribs = []
    s = len(model.__name__) + 1
    for c in model.__mapper__.iterate_properties:
        if isinstance(c, RelationshipProperty):
            attribs.append(str(c)[s:])
    return attribs


def _select(model, *fields):
    
    from sqlalchemy.orm import defer, lazyload

    PK_COLUMNS = _get_pk(model)
    COLUMNS = _get_columns(model)
    RELATED = _get_relations(model)
    ATTRIBUTES = _get_columns(model) + _get_relations(model) + _get_custom(model)

    fields = list(set(fields)) if fields else COLUMNS

    # select all column properties if none is specified
    for attr in fields:
        if attr in COLUMNS:
            break
    else:
        fields.extend(COLUMNS)

    options = []
    # ensure PKs are included and defer unrequested attributes (includes related)
    for attr in ATTRIBUTES:
        if attr not in fields:
            if attr in PK_COLUMNS:
                fields.append(attr)
            elif attr in COLUMNS:
                options.append(defer(attr))
            # relationships
            elif attr in RELATED:
                options.append(lazyload(attr))
            # user-defined column_property are deferred by default unless
            # specified in the custom_properties tuple or within the select
            elif attr not in model.custom_properties:
                options.append(defer(attr))    
    return options


def _where(model, *criteria, **filters):
    """Builds a list of where conditions for this applying the correct operators
    for representing the values.
    
    For sequence values of list, set or tuples, the SQL `IN` operator is used.
    For single values, the SQL `=` operator.
    """
    conditions = []
    conditions.extend(criteria)
    # build criteria from filters
    if filters:
        COLUMNS = _get_columns(model)
        COLUMN_TYPES = {c.name:c for c in model.__table__.columns}

        for attr in filters:
            assert attr in COLUMNS, "Invalid attribute in criteria %r" % attr

            value = filters[attr]
            c = COLUMN_TYPES[attr]

            if not isinstance(value, (list,tuple,set)):
                value = [value]

            # generate appropriate criteria expression for datetime filters
            import datetime as dt
            if c.type.python_type == dt.datetime:
                lower = min(value)
                upper = max(value)
                lower = dt.datetime(year=lower.year, month=lower.month, day=lower.day,)
                upper = dt.datetime(year=upper.year, month=upper.month, day=upper.day,
                                    hour=23, minute=59, second=59)
                value = getattr(model,attr).between(lower, upper)
            elif len(value) == 1:
                value = getattr(model,attr) == value.pop()
            else:
                value = getattr(model,attr).in_(value)                
            conditions.append(value)
    return conditions


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

    #user-defined column_property objects to eager load when fetching mapped object.
    #properties are also returned in to_json by default
    custom_properties = tuple()

    def __init__(self, **params):
        self.assign_attributes(**params)

    def assign_attributes(self, **params):
        for attr in params:
            if attr in self.attr_protected: continue
            if attr in self.attr_accessible or not self.attr_accessible:
                if hasattr(self, attr):
                    setattr(self, attr, params[attr])
        return self

    def update_attributes(self, **params):
        self.assign_attributes(**params)
        return self.put()

    def save(self):
        self.query.session.add(self)
        return self

    def put(self):
        self.save()
        self.query.session.commit()
        return self

    def as_json(self, include_columns=None):
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
    def select_by(cls, *fields):
        """Combines a SQL projection and selection in one step by returning a curried
        function of a where clause
        Eg. User.select_by('id','name')(name='Francis).all()
        """        
        def whereclause(*criteria, **filters):
            return cls.select(*fields).filter(*_where(cls, *criteria, **filters))            
        return whereclause

    @classmethod
    def select(cls, *fields):
        options = _select(cls, *fields)
        return cls.query.options(*options)

    @classmethod
    def where(cls, *criteria, **filters):
        conditions = _where(cls, *criteria, **filters)
        return cls.select().filter(*conditions) 