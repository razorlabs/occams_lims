from zope import interface
import zope.schema
from plone.directives import form

from hive.lab import MessageFactory as _

class ILab(form.Schema):
    """
    An Interface for the Labs
    """
    
    
class IClinicalLab(ILab):
    """
    An Interface for the Labs
    """

class IResearchLab(ILab):
    """
    An Interface for the Labs
    """
