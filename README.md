
## About
A collections of common utilities extracted from my Flask applications and useful snippets from [flask.pocco.org](flask.pocco.org)

The files are mostly independent from each other but may have dependencies on some
Flask extensions. The helpers.py module however has dependencies on decorators.py

## Files
 - decorators.py   = common decorators for application routes
 - filters.py      = filters for template engines
 - mimes.py        = mimes type utility functions
 - validators.py   = common validation functions for user input
 - helpers.py      = utility functions for use with flask context offering Rails style template helpers. 
 - routing.py      = wrappers for blueprints and request handlers. Require `decorators.py`
 - sessions/       = alternative session implementations to replace default Flask session interface

More documentation to come later.

