from datetime import date
from zope import interface
import zope.schema
from plone.directives import form

from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel
from hive.lab import utilities as utils

class IViewableAliquot(form.Schema):
    aliquot_id = zope.schema.TextLine(
        title=u"Aliquot #",
        readonly=True
        )

    patient_title = zope.schema.TextLine(
        title=u"Patient OUR#",
        readonly=True
        )

    patient_legacy_number = zope.schema.TextLine(
        title=u"Patient Legacy (AEH) Number",
        readonly=True
        )

    study_title = zope.schema.TextLine(
        title=u"Study",
        readonly=True
        )
 
    protocol_title = zope.schema.TextLine(
        title=u"Protocol Week",
        readonly=True
        )

    pretty_aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=utils.SpecimenAliquotVocabulary(u"aliquot_type")
        )
      
  
class IAliquotLabel(interface.Interface):

    aliquot = zope.schema.TextLine(title=u"Aliquot Number")

    our = zope.schema.TextLine(title=u"OUR #")

    study = zope.schema.TextLine(title=u"Study")

    week = zope.schema.TextLine(title=u"Week")

    type = zope.schema.TextLine(title=u"Type")

    date = zope.schema.Date(title=u"Storage Date")


class IAliquotBlueprint(form.Schema):
    """
    Blueprint the system can use to create aliquot
    """
    title = zope.schema.TextLine(
        title=_(u'Aliquot Title'),
        )
        
    aliquot_type_title = zope.schema.TextLine(
        title=_(u'Aliquot Type Title'),
        )
    aliquot_type = zope.schema.TextLine(
        title=_(u'Aliquot Type Value'),
        )

    default_volume = zope.schema.Float(
        title=_(u'Default volume'),
        required=False,
        )
    measure = zope.schema.TextLine(
        title=_(u'Volume Measurement'),
        )
        
    default_count = zope.schema.Float(
        title=_(u'Default cell count'),
        required=False,
        )
    measure = zope.schema.TextLine(
        title=_(u'Volume Measurement'),
        )
    special_instructions = zope.schema.List(
        title=_(u'Special Instruction Options'),
        value_type = zope.schema.TextLine(),
        required=False
        )
        
class IAliquotLabel(ILabel):
    """
    A Specimen Label
    """
    
    pretty_aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=utils.SpecimenAliquotVocabulary(u"aliquot_type")
        ) 