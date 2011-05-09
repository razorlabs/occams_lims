from datetime import date
from zope import interface
import zope.schema
from plone.directives import form

from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel
from hive.lab import vocabularies

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
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type")
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

    default_count = zope.schema.Int(
        title=_(u'Default Count'),
        description=_(u'Default number of aliquot expected from the specimen')
        default=1,
        required=True
        )
    aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type")
        )

    volume = zope.schema.Float(
        title=_(u"Volume (mLs)"),
        required=False,
        )
        
    cell_amount = zope.schema.Float(
        title=_(u"# of cells (x10^6)"),
        description=_(u"measured in millions"),
        required=False,
        )
        
    storage_site = zope.schema.Choice(
        title=_(u"Storage Site"),
        description=_(u"Please select the appropriate location:"),
        source=SpecimenAliquotVocabulary(u"aliquot_storage_site"),
        required=True,
        default=u'richman lab'
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
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type")
        ) 