from datetime import date

from zope import interface
from zope.schema.fieldproperty import  FieldProperty
import zope.schema

from five import grok
from plone.directives import form

from avrc.aeh import MessageFactory as _
from avrc.aeh.browser import widget
from avrc.aeh.specimen import utilities as utils
from avrc.aeh.specimen.utilities import SpecimenAliquotVocabulary

from avrc.data.store.interfaces import IAliquot as IDSAliquot
from avrc.data.store.lab import Aliquot as DSAliquot

class IAliquot(form.Schema):
    """ Base class for aliquot data """

    form.mode(dsid='hidden')
    dsid = zope.schema.Int(
        title=u"DataStore ID",
        required=False
        )

    form.mode(specimen_dsid='hidden')
    specimen_dsid = zope.schema.Int(
        title=u"Specimen data store id",
        required=False
        )

    form.mode(aliquot_id='display')
    aliquot_id = zope.schema.TextLine(
        title=u"ID",
        required=False
        )

    form.mode(aliquot_type='hidden')
    aliquot_type = zope.schema.Choice(
        title=_(u"Type"),
        source=SpecimenAliquotVocabulary(u"aliquot_type"),
        )

    form.omitted('state')
    state = zope.schema.Choice(
        title=_(u"State"),
        source=SpecimenAliquotVocabulary(u"aliquot_state"),
        required=False
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

    store_date = zope.schema.Date(
        title=_(u"Store Date"),
        required=False
        )

    freezer = zope.schema.TextLine(
        title=_(u"Freezer"),
        required=False,
        )

    rack = zope.schema.TextLine(
        title=_(u"Rack"),
        required=False,
        )

    box = zope.schema.TextLine(
        title=_(u"Box"),
        required=False,
        )

    storage_site = zope.schema.Choice(
        title=_(u"Storage Site"),
        description=_(u"Please select the appropriate location:"),
        source=SpecimenAliquotVocabulary(u"aliquot_storage_site"),
        required=False
        )

    form.widget(notes=widget.SmallTextAreaFieldWidget)
    notes = zope.schema.Text(
        title=_(u"Notes:"),
        required=False
        )

    form.fieldset(
        'tracking',
        label=_(u'Tracking'),
        fields=['analysis_status', 'sent_date', 'sent_site', 'sent_name',
                'sent_notes']
        )
    form.omitted('analysis_status')
    analysis_status = zope.schema.Choice(
        title=_(u"Sent for analysis?"),
        source=SpecimenAliquotVocabulary(u"aliquot_state"),
        required=False
        )

    sent_date = zope.schema.Date(
        title=_(u"Date sent"),
        required=False
        )

    form.mode(thawed_num='hidden')
    thawed_num = zope.schema.Int(
        title=_(u"Number of times thawed."),
        default=0,
        required=False,
        )

    sent_site = zope.schema.Choice(
        title=_(u"Where was it sent?"),
        description=_(u"Please select the appropriate location:"),
        source=SpecimenAliquotVocabulary(u"aliquot_sent_site"),
        required=False
        )

    sent_name = zope.schema.TextLine(
        title=_(u"Who was it sent to?"),
        description=_(u"Please enter the name of the person the aliquot was "
                      u"sent to OR the name of the person who placed the "
                      u"sample on hold:"),
        required=False,
        )

    form.widget(sent_notes=widget.SmallTextAreaFieldWidget)
    sent_notes = zope.schema.Text(
        title=_(u"Notes about delivery:"),
        required=False
        )

    form.omitted('special_instruction')
    special_instruction = zope.schema.Choice(
        title=_(u"Special"),
        source=SpecimenAliquotVocabulary(u"aliquot_special_instruction"),
        required=False,
        )

    aliquot_count = zope.schema.Int(
        title=u"Aliquot Count",
        required=False
        )

    patient_title = zope.schema.TextLine(
        title=u"Patient OUR#",
        required=False
        )

    patient_legacy_number = zope.schema.TextLine(
        title=u"Legacy (AEHID) Number",
        missing_value=u"",
        required=False,
        )

    study_title = zope.schema.TextLine(
        title=u"Study",
        required=False
        )

    protocol_title = zope.schema.TextLine(
        title=u"Protocol Week",
        required=False
        )

    siblings = zope.schema.List(
        title=u"siblings",
        required=False,
        value_type=zope.schema.TextLine(title=u"Aliquot IDs")
        )

@form.default_value(field=IAliquot['store_date'])
def dateCollectedValue(data):
    return date.today()


class IAliquotLabel(interface.Interface):

    aliquot = zope.schema.TextLine(title=u"Aliquot Number")

    our = zope.schema.TextLine(title=u"OUR #")

    study = zope.schema.TextLine(title=u"Study")

    week = zope.schema.TextLine(title=u"Week")

    type = zope.schema.TextLine(title=u"Type")

    date = zope.schema.Date(title=u"Storage Date")
# 
# @grok.adapter(IAliquot)
# @grok.implementer(IDSAliquot)
# def AliquotToDSAliquot(context):
#     """ Translates an AEH aliquot to a data store aliquot """
#     obj = DSAliquot()
#     obj.dsid = getattr(context, "dsid", None)
#     obj.type = context.aliquot_type
#     obj.specimen_dsid = context.specimen_dsid
#     obj.state = context.state
#     obj.volume = context.volume
#     obj.cell_amount = context.cell_amount
#     obj.store_date = context.store_date
#     obj.freezer = context.freezer
#     obj.rack = context.rack
#     obj.box = context.box
#     obj.storage_site = context.storage_site
#     obj.thawed_num = context.thawed_num
#     obj.analysis_status = context.analysis_status
#     obj.sent_date = context.sent_date
#     obj.sent_name = context.sent_name
#     obj.notes = context.notes
#     obj.special_instruction = context.special_instruction
#     return obj
# 
# @grok.adapter(IDSAliquot)
# @grok.implementer(IAliquot)
# def DSAliquotToAliquot(context):
#     """ Translates a data store aliquot to an AEH aliquot """
#     obj = Aliquot()
#     obj.dsid = context.dsid
#     obj.aliquot_id = unicode(1000000 + int(context.dsid))
#     obj.aliquot_type = context.type
#     obj.specimen_dsid = context.specimen_dsid
#     obj.state = context.state
#     obj.volume = context.volume
#     obj.cell_amount = context.cell_amount
#     obj.store_date = context.store_date
#     obj.freezer = context.freezer
#     obj.rack = context.rack
#     obj.box = context.box
#     obj.storage_site = context.storage_site
#     obj.thawed_num = context.thawed_num
#     obj.analysis_status = context.analysis_status
#     obj.sent_date = context.sent_date
#     obj.sent_name = context.sent_name
#     obj.notes = context.notes
#     obj.special_instruction = context.special_instruction
#     return obj
# 
