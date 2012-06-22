#!/usr/bin/env python

import datetime as dt
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, abort


class _SQLAlchemyExt(SQLAlchemy):
     
    def commit(self):
        return self.session.commit()
    
    def rollback(self):
        return self.session.rollback()
    
    def execute(self, obj,*multiparams,**params):
        conn = self.engine.connect()
        result = conn.execute(obj,*multiparams,**params)
        return result
    
    def add(self, model):
        self.session.add(model)
    
    def remove(self):
        self.session.remove()
    
    def query(self, *args, **kwargs):
        return self.session.query(*args, **kwargs)

db = _SQLAlchemyExt()

class ModelMixin(object):
    """Provives an extended query function with some Rails style candy,
    for db.Model classes defined for SQLAlchemy.
    
    Example:
    
    class User(ModelMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True)
        email = db.Column(db.String(120), unique=True)
        addresses = db.relationship('Address', backref='user',lazy='joined')
        
    class Address(ModelMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        city = db.Column(db.String(50))
        state = db.Column(db.String(50))
        street = db.Column(db.String(50))
        number = db.Column(db.Integer)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))    
    """
    
    #attributes protected from mass assignment
    attr_protected = tuple()
    
    #attributes accessible through mass assignments
    attr_accessible = tuple()
    
    #user-defined column_property objects to eager load when fetching mapped object.
    default_properties = tuple()
    
    def __init__(self, **params):
        self.assign_attributes(**params)
        
    def assign_attributes(self, **params):
        for attr in params:
            if attr in self.__class__.attr_protected: continue
            if attr in self.__class__.attr_accessible or not self.__class__.attr_accessible:
                assert hasattr(self, attr), 'Unknown attribute: %s' % attr
                setattr(self, attr, params[attr])
        return self
    
    def update_attributes(self, **params):
        self.assign_attributes(**params)
        return self.put()        
    
    def save(self):
        db.session.add(self)
        return self
    
    def put(self):        
        self.save()
        db.session.commit()
        return self
    
    def to_json(self):
        return jsonify({c.name:getattr(self, c.name) for c in self.__table__.columns})
    
    @classmethod
    def get(cls,ident):
        return db.session.query(cls).get(ident)
    
    @classmethod
    def get_or_abort(cls, ident, code=404):
        """Get an object with his given id or an abort error (404 is the default)
        """
        value = cls.get(ident)
        if value is None:
            abort(code)
        return value

    @classmethod
    def query(cls,*fields,**filters):
        """Provides a simple interface for constructing a query dynamically
        for a target mapper `class`.
    
        A subset of attributes to load can be given to avoid generating a large result.
    
        Ex. User.query('name','email')
    
        Related attributes and user-defined column properties are lazy loaded by default.
        To eager load them, just provide their names in the query.
        
        The configured loader for the attribute in the mapping will be used.
        This query loads the column_property `address_count` and the related property `addresses`
        
        Ex: User.query('address_count', 'addresses')
        
        Alternatively, you can add the loading option directly (applies to related properties)
        Ex: User.query('id',subqueryload('addresses'))
    
        Primary Key attributes of the `class` are always returned.
        All column attributes of the `class` are returned if none is specfied.     
    
        """
        from sqlalchemy.orm import defer, lazyload, ColumnProperty, RelationshipProperty
        from sqlalchemy.orm.interfaces import MapperOption
        from sqlalchemy.sql.expression import ClauseElement
    
    
        COLUMN_TYPES = {c.name:c for c in cls.__table__.columns}
        COLUMNS = COLUMN_TYPES.keys()
        PK_COLUMNS = [c.name for c in cls.__table__.primary_key]
                
        s = len(cls.__name__) + 1 # class_name + '.'
        PROPERTIES = {str(c)[s:] : c.__class__ for c in cls.__mapper__.iterate_properties}
    
        ATTRIBUTES = PROPERTIES.keys()
        options, criteria = [], []
    
        if not fields:
            fields = COLUMNS
        else:
            fields = list(set(fields))
            for item in fields[:]:
                # filter for conditions
                if isinstance(item, ClauseElement):
                    criteria.append(item)
                    fields.remove(item)
                # filter for options
                elif isinstance(item, MapperOption):
                    print item
                    options.append(item)
                    fields.remove(item)
                # validate columns
                else:
                    assert item in ATTRIBUTES, "Invalid attribute %r." % str(item)   
    
        # select all column properties if none is specified
        for attr in fields:
            if attr in COLUMNS:
                break
        else:
            fields.extend(COLUMNS)
                    
        # ensure PKs are included and defer unrequested attributes (includes related)
        for attr in ATTRIBUTES:
            if attr not in fields:
                if attr in PK_COLUMNS:
                    fields.append(attr)
                elif attr in COLUMNS:                            
                    options.append(defer(attr))                
                # relationships
                elif issubclass(PROPERTIES[attr], RelationshipProperty):
                    options.append(lazyload(attr))                
                # user-defined column_property are deferred unless specified in
                # the default_properties tuple or within the query
                elif attr not in cls.default_properties:
                    options.append(defer(attr))
        
        # build criteria from filters
        if filters:
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
                    value = getattr(cls,attr).between(lower, upper)
                elif len(value) == 1:
                    value = getattr(cls,attr) == value.pop()
                else:
                    value = getattr(cls,attr).in_(value)                
                criteria.append(value)
        
        return db.query(cls).options(*options).filter(*criteria) 