#!/usr/bin/env python

import datetime as dt
from flask_sqlalchemy import SQLAlchemy


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
    mapped = _get_mapper(obj)
    return [key.name for key in mapped.primary_key]

def _get_columns(model):
    """Returns a dictionary-like object containing all the columns of the
    specified `model` class.

    """
    return {c.key:c for c in _get_mapper(model).iterate_properties
                if isinstance(c, ColumnProperty)}


def _get_relations(model):
    return {c.key:c for c in _get_mapper(model).iterate_properties
                if isinstance(c, RelationshipProperty)}


# This code was adapted from :meth:`elixir.entity.Entity.to_dict` and
# http://stackoverflow.com/q/1958219/108197.
#
# TODO should we have an `include` argument also?
def _to_dict(instance, deep=None, exclude=None):
    """Returns a dictionary representing the fields of the specified `instance`
    of a SQLAlchemy model.

    `deep` is a dictionary containing a mapping from a relation name (for a
    relation of `instance`) to either a list or a dictionary. This is a
    recursive structure which represents the `deep` argument when calling
    `_to_dict` on related instances. When an empty list is encountered,
    `_to_dict` returns a list of the string representations of the related
    instances.

    `exclude` specifies the columns which will *not* be present in the returned
    dictionary representation of the object.

    """
    deep = deep or {}
    exclude = exclude or ()
    # create the dictionary mapping column name to value
    columns = (p.key for p in object_mapper(instance).iterate_properties
               if isinstance(p, ColumnProperty))
    result = dict((col, getattr(instance, col)) for col in columns)
    # Convert datetime and date objects to ISO 8601 format.
    #
    # TODO We can get rid of this when issue #33 is resolved.
    for key, value in result.items():
        if isinstance(value, datetime.date):
            result[key] = value.isoformat()
    # recursively call _to_dict on each of the `deep` relations
    for relation, rdeep in deep.iteritems():
        # exclude foreign keys of the related object for the recursive call
        relationproperty = object_mapper(instance).get_property(relation)
        newexclude = (key.name for key in relationproperty.remote_side)
        # get the related value so we can see if it is None or a list
        relatedvalue = getattr(instance, relation)
        if relatedvalue is None:
            result[relation] = None
        elif isinstance(relatedvalue, list):
            result[relation] = [_to_dict(inst, rdeep, newexclude)
                                for inst in relatedvalue]
        else:
            result[relation] = _to_dict(relatedvalue, rdeep, newexclude)
    return result


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
    for attr in (c.key for c in class_mapper(model).iterate_properties):
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

    For sequence values of list, set or tuples, the SQL `IN` operator is used.
    For single values, the SQL `=` operator.
    """
    conditions = []
    conditions.extend(criteria)
    # build criteria from filters
    if filters:
        COLUMNS = _get_columns(model)

        for attr in filters:

            value = filters[attr]
            prop = COLUMN[attr]

            if not isinstance(value, (list,tuple,set)):
                value = [value]

            # generate appropriate criteria expression for datetime filters
            if prop.type.python_type == dt.datetime:
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
