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

class IResearchLab(ILab):
    """
    An Interface for the Labs
    """
    pass

class IFilterForm(form.Schema):
    """
    """
    patient = zope.schema.TextLine(
        title=_(u"Patient id"),
        description=_(u"Patient OUR#, Legacy AEH ID, or Masterbook Number"),
        required=False
        )

    after_date = zope.schema.Date(
        title=_(u"Sample Date"),
        description=_(u"Samples on this date. If Limit Date is set as well, will show samples between those dates"),
        required=False

        )

    before_date = zope.schema.Date(
        title=_(u"Sample Limit Date"),
        description=_(u"Samples before this date. Only applies if Sample Date is also set"),
        required=False
        )

    show_all = zope.schema.Bool(
        title=_(u"Show all Samples"),
        description=_(u"Show all samples, including missing, never drawn, checked out, etc"),
        required=False
        )