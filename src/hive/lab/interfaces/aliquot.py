from datetime import date
from zope import interface
import zope.schema
from plone.directives import form
from beast.browser import widgets
from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel
from hive.lab import vocabularies

class IAliquot(interface.Interface):
    """ Mostly copied from aeh forms. Tons of work to do still. """

    dsid = zope.schema.Int(
        title=_(u'Data Store Id'),
        required=False,
        )

    specimen_dsid = zope.schema.Int(
        title=_(u'Data Store Specimen Id'),
        required=False,
        )
    type = zope.schema.TextLine(
        title=_(u'Type'),
        )

    state = zope.schema.TextLine(
        title=_(u'State'),
        required=False
        )

    volume = zope.schema.Float(
        title=u'Volume (in ml.)',
        required=False,
        )

    cell_amount = zope.schema.Float(
        title=_(u'Number of cells'),
        description=_(u'measured in 10,000 increments'),
        required=False,
        )

    store_date = zope.schema.Date(
        title=_(u'Store Date'),
        required=False
        )

    freezer = zope.schema.TextLine(
        title=_(u'Freezer'),
        required=False,
        )

    rack = zope.schema.TextLine(
        title=_(u'Rack'),
        required=False,
        )

    box = zope.schema.TextLine(
        title=_(u'Box'),
        required=False,
        )

    thawed_num = zope.schema.Int(
        title=_(u'Number of times thawed.'),
        required=False,
        )

    analysis_status = zope.schema.TextLine(
        title=_(u'Sent for analysis?'),
        required=False
        )

    sent_date = zope.schema.Date(
        title=_(u'Date sent'),
        required=False
        )

    storage_site = zope.schema.TextLine(
        title=_(u'The site where aliquot was sent'),
        required=False
        )

    sent_name = zope.schema.TextLine(
        title=_(u'Who recieved the aliquot'),
        description=_(u'Please enter the name of the person the aliquot was sent to '
                u'OR the name of the person who placed the sample '
                u'on hold:'),
        required=False,
        )
        
    sent_notes = zope.schema.Text(
        title=_(u'Notes on this aliquot (if any):'),
        required=False
        )
        
    notes = zope.schema.Text(
        title=_(u'Notes on this aliquot (if any):'),
        required=False
        )

    special_instruction = zope.schema.TextLine(
        title=_(u'Special'),
        description=u'',
        required=False,
        )

class IViewableAliquot(IAliquot, form.Schema):
    """
    """
    dsid = zope.schema.TextLine(
        title=u"Aliquot #",
        readonly=True
        )

    state = zope.schema.Choice(
        title=_(u"State"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_state"),
        required=False
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

    study_week = zope.schema.TextLine(
        title=u"Study/Week",
        readonly=True
        )
    vol_count = zope.schema.TextLine(
        title=_(u'Volume / Cell Count'),
        readonly=True,
        )

    frb = zope.schema.TextLine(
        title=_(u'Freezer / Rack / Box'),
        readonly=True,
        )

    pretty_aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type")
        )

    special_instruction = zope.schema.Choice(
        title=_(u"Special"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_special_instruction"),
        required=True,
        )
 
    thawed = zope.schema.Bool(
        title=_(u'Thawed'),
        required = False
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
        value_type=zope.schema.TextLine(),
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
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type"), required=False
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
