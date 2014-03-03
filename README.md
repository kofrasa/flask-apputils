## About ##
Common utilities extracted from my Flask applications and useful snippets from [flask.pocco.org](flask.pocco.org)

The files are mostly independent from each other but may have dependencies on some
Flask extensions. The helpers.py module however has dependencies on decorators.py

## Modules ##
* decorators.py   = common decorators for application routes
* filters.py      = filters for templating frameworks
* middlewares.py  = useful middleware implementations
* mimes.py        = mimes type utility functions
* validators.py   = common validation functions for user input
* helpers.py      = utility classes and functions functions for repeated patterns. Depends on decorators.py
* active_record.py = provides rails style ActiveRecord mixin for extending Flask-SQLAlchemy's Model
                     with a simpler query interface and automatic json serialization
* active_document.py = provides a similar active_record interface for mongodb extending MongoAlchemy's Document
* sessions/       = alternative session implementations to replace default Flask session interface


More documentation to come later.

