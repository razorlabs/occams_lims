import zope.schema
from plone.directives import form

import zope.interface

from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabelSheet
from hive.lab.interfaces.aliquot import IAliquotFilter


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

class IResearchLab(ILab, IAliquotFilter):
    """
    An Interface for the Labs
    """
    pass
