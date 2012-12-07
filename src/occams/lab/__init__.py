  # -*- extra stuff goes here -*-
import logging
import zope.i18nmessageid

MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

Logger = logging.getLogger(__name__)

from avrc.aeh import FIA_SCOPED_SESSION_KEY as SCOPED_SESSION_KEY
from avrc.aeh import FiaSession as Session

FILTER_KEY = "occams.lab.filter"

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
