from datetime import date
from zope import interface
import zope.schema
from plone.directives import form

from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel
from hive.lab import vocabularies
from avrc.data.store.interfaces import IAliquot
class IViewableAliquot(IAliquot, form.Schema):
    """
    """
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

    special_instruction = zope.schema.Choice(
        title=_(u"Special"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_special_instruction"),
        default=u'na',
        required=False,
        )

class IAliquotFilter(interface.Interface):

    def getAliquotFilter(basekw, states):
        """
        Return a dictionary of keywords to use in filtering available aliquot
        """
        
        
class IAliquotSupport(interface.Interface):
    """
    Marker interface to search for aliquot associated with a specific item
    """


class IAliquotBlueprint(IAliquotSupport, IAliquotFilter, form.Schema):
    """
    Blueprint the system can use to create aliquot
    """

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
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_storage_site"),
        required=True,
        default=u'richman lab'
        )
        
    special_instructions = zope.schema.List(
        title=_(u'Special Instruction Options'),
        value_type = zope.schema.TextLine(),
        required=False
        )
        
        

class IAliquotGenerator(form.Schema):
    count = zope.schema.Int(
        title=_(u'Count'),
        description=_(u'Number of aliquot to generate from the specimen'),
        required=False
        )
#     blueprint_zid = zope.schema.TextLine(
#         title=u"Blueprint",
#         readonly=True
#         )

class IAliquotLabel(ILabel):
    """
    A Specimen Label
    """
    
    pretty_aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type")
        ) 


class IAliquotFilterForm(form.Schema):
    """
    """
    patient = zope.schema.TextLine(
        title=_(u"Patient id"),
        description=_(u"Patient OUR#, Legacy AEH ID, or Masterbook Number"),
        required=False
        )

    type = zope.schema.Choice(title=u"Type of Aliquot",
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type"),        required=False
        )
        
    after_date = zope.schema.Date(
        title=_(u"Aliquot Date"),
        description=_(u"Aliquot on this date. If Limit Date is set as well, will show aliquot between those dates"),
        required=False

        )
 
    before_date = zope.schema.Date(
        title=_(u"Aliquot Limit Date"),
        description=_(u"Aliquot before this date. Only applies if Aliquot Date is also set"),
        required=False
        )
    
    show_all = zope.schema.Bool(
        title=_(u"Show all Aliquot"),
        description=_(u"Show all aliquot, including missing, never drawn, checked out, etc"),
        required=False
        )