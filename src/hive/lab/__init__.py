  # -*- extra stuff goes here -*- 
import logging
import zope.i18nmessageid
from avrc.aeh import FIA_SCOPED_SESSION_KEY

MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

Logger = logging.getLogger(__name__)

SCOPED_SESSION_KEY = FIA_SCOPED_SESSION_KEY

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
