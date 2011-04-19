  # -*- extra stuff goes here -*- 
import logging

import zope.i18nmessageid

MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

Logger = logging.getLogger(__name__)

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
