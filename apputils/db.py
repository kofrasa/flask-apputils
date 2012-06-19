# -*- coding: utf-8 -*-

import datetime as dt
from math import ceil
from sqlalchemy.orm import scoped_session, create_session, Query
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask import jsonify, abort

__all__ = [
    'Base',
    'Pagination',
    'commit',
    'rollback',
    'execute',
    'add',
    'remove',
    'query',    
    'create_all',
    'drop_all',
    'init_engine',
    'init_app'
]


class BaseQuery(Query):
    """The default query object used for models, and exposed as
    :attr:`~SQLAlchemy.Query`. This can be subclassed and
    replaced for individual models by setting the :attr:`~Model.query_class`
    attribute.  This is a subclass of a standard SQLAlchemy
    :class:`~sqlalchemy.orm.query.Query` class and has all the methods of a
    standard query as well.
    """

    def get_or_404(self, ident):
        """Like :meth:`get` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.get(ident)
        if rv is None:
            abort(404)
        return rv

    def first_or_404(self):
        """Like :meth:`first` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.first()
        if rv is None:
            abort(404)
        return rv

    def paginate(self, page, per_page=20, error_out=True):
        """Returns `per_page` items from page `page`.  By default it will
        abort with 404 if no items were found and the page was larger than
        1.  This behavor can be disabled by setting `error_out` to `False`.

        Returns an :class:`Pagination` object.
        """
        if error_out and page < 1:
            abort(404)
        items = self.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)
        return Pagination(self, page, per_page, self.count(), items)


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        return int(ceil(self.total / float(self.per_page)))

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:

        .. sourcecode:: html+jinja

            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>...</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


class Base(object):
    """Base class for objects mapping tables.
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
        db.add(self)
        return self
    
    def put(self):        
        self.save()
        db.commit()
        return self
    
    def to_json(self):
        return jsonify({c.name:getattr(self, c.name) for c in self.__table__.columns})
    
    @classmethod
    def get(cls,ident):
        return db.query(cls).get(ident)
    
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
    
        Mapped attributes are lazy loaded by default. To eager load a mapped
        attribute on the given class, just provide its name as part of the fields.
    
        Ex: User.query('contacts')
    
        A smart guess is taken to use either, joinedload or subqueryload.
        For more fine grain control, especially in the case of odd names, use an
        explicit mapper option construct.
    
        Ex: User.query('id',subqueryload('addresses'))
    
        All simple attributes of the `class` are returned if none is specfied.
        Primary Key attributes of the `class` are always returned.
    
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
                                
                # generate appropriate criteria expression
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


engine = None
db = scoped_session(lambda: create_session(bind=engine, autoflush=True, autocommit=False))
db.query_cls = BaseQuery
Base = declarative_base(cls=Base)


def init_engine(uri, **kwargs):
    global engine
    engine = create_engine(uri, **kwargs)
    return engine

def create_all():
    Base.metadata.create_all(engine)

def drop_all():
    Base.metadata.drop_all(engine)

def commit():
    return db.commit()

def rollback():
    return db.rollback()

def execute(obj,*multiparams,**params):
    conn = engine.connect()
    result = conn.execute(obj,*multiparams,**params)
    return result

def add(model):
    db.add(model)

def remove():
    db.remove()

def query(*args, **kwargs):
	return db.query(*args, **kwargs)

def init_app(app):
    """Initialize application database"""
    init_engine(app.config['DATABASE_URI'], echo=app.config.get('DATABASE_ECHO'),
                pool_recycle=app.config.get('DATABASE_POOL_RECYCLE'))
