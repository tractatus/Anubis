"Proposals review handling system."

import re

__version__ = '0.5.14'

class Constants:
    VERSION     = __version__
    SOURCE_NAME = 'Anubis'
    SOURCE_URL  = 'https://github.com/pekrau/Anubis'

    BOOTSTRAP_VERSION  = '4.3.1'
    JQUERY_VERSION     = '3.3.1'
    DATATABLES_VERSION = '1.10.18'

    ID_RX    = re.compile(r'^[a-z][a-z0-9_]*$', re.I)
    IUID_RX  = re.compile(r'^[a-f0-9]{32,32}$', re.I)
    EMAIL_RX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    # CouchDB document types
    USER     = 'user'
    CALL     = 'call'
    PROPOSAL = 'proposal'
    REVIEW   = 'review'
    DECISION = 'decision'
    LOG      = 'log'

    # User roles
    ADMIN = 'admin'
    # USER  = 'user' # Defined above
    USER_ROLES = (ADMIN, USER)

    # User statuses
    PENDING  = 'pending'
    ENABLED  = 'enabled'
    DISABLED = 'disabled'
    USER_STATUSES = (PENDING, ENABLED, DISABLED)

    # User capacities (per call)
    SUBMITTER = 'submitter'
    REVIEWER  = 'reviewer'

    # Input field types
    TEXT     = 'text'
    LINE     = 'line'
    BOOLEAN  = 'boolean'
    INTEGER  = 'integer'
    FLOAT    = 'float'
    SCORE    = 'score'
    DOCUMENT = 'document'
    FIELD_TYPES = (TEXT, LINE, BOOLEAN, INTEGER, FLOAT, SCORE, DOCUMENT)

    # Content types
    HTML_MIMETYPE = 'text/html'
    JSON_MIMETYPE = 'application/json'

    # Misc
    JSON_SCHEMA_URL = 'http://json-schema.org/draft-07/schema#'

    def __setattr__(self, key, value):
        raise ValueError('cannot set constant')


constants = Constants()
