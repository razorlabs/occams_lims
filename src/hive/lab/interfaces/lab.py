import zope.schema
from plone.directives import form
from hive.lab import MessageFactory as _
import zope.interface
from z3c.relationfield.schema import RelationChoice, RelationList
from plone.formwidget.contenttree import ObjPathSourceBinder
from plone.app.dexterity.behaviors.related import IRelatedItems
from hive.lab.interfaces.specimen import ISpecimenBlueprint
from hive.lab.vocabularies import SpecimenVocabulary

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
