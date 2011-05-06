import zope.schema
from plone.directives import form

from hive.lab import MessageFactory as _
import zope.interface

class IContainsSpecimen(zope.interface.Interface):
    """
    Marker interface for items that contain Specimen Blueprints
    """
    pass
    
    
class ILab(form.Schema, IContainsSpecimen):
    """
    An Interface for the Labs
    """
    pass
    
class IClinicalLab(ILab):
    """
    An Interface for the Labs
    """
    pass
    
class IResearchLab(ILab):
    """
    An Interface for the Labs
    """
    pass
