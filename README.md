## About ##
Utilities extracted from my Flask applications.

The files are mostly independent from each other but may have dependencies on some
Flask extensions.

## Modules ##
* decorators.py   = common decorators for apps
* filters.py      = filters to plugin into template framework
* interfaces.py   = middlewares and secure cookie implementations
* mimes.py        = list of mimes and common extensions
* validators.py   = common validation functions for user input
* helpers.py      = utility functions mainly to save some typing
* -logging        = poor man's logging shortcut (avoid using this for now!)
* sqlalchemy_ext  = extension to the Flask-SQLAlchemy plus an ActiveRecord mixin
                    for modles which provides useful query functions

## Dependencies ##
* Flask-HTMLBuilder
* Flask-SQLAlchemy
* itsdangerous


Personalization is priceless for those of us who choose not to wear straight jackets. :)

More documentation to come later.