from datetime import datetime
from datetime import date

from zope import component
from zope import interface
import zope.schema

from five import grok
from hive.lab import MessageFactory as _
from plone.directives import form

from hive.lab import vocabularies


class ILabelSheet(form.Schema):
    """
        info for building a pdf of labels
    """
    page_height = zope.schema.Decimal(
        title=_(u"Page Height"),
        required=True
        )
        
    page_width = zope.schema.Decimal(
        title=_(u"Page Width"),
        required=True
        )

    top_margin = zope.schema.Decimal(
        title=_(u"Top Margin"),
        required=True
        )
    side_margin = zope.schema.Decimal(
        title=_(u"Side Margin"),
        required=True
        )
    vert_pitch = zope.schema.Decimal(
        title=_(u"Vertical Pitch"),
        required=True
        )
        
    horz_pitch = zope.schema.Decimal(
        title=_(u"Horizontal Pitch"),
        required=True
        )
    label_height = zope.schema.Decimal(
        title=_(u"Label Height"),
        required=True
        )
    label_width = zope.schema.Decimal(
        title=_(u"Label Width"),
        required=True
        )
        
    label_round = zope.schema.Decimal(
        title=_(u"Label Round"),
        required=True
        )

    no_across = zope.schema.Int(
        title=_(u"Number Across"),
        required=True
        )

    no_down = zope.schema.Int(
        title=_(u"Number Down"),
        required=True
        )

class ILabel(interface.Interface):
    """
    Class that supports transforming an object into a label.
    """        
    patient_title = zope.schema.TextLine(
        title=u"Patient OUR#",
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
 
    date_collected = zope.schema.Date(
        title=u"Date",
        readonly=True
        )  
 
class ISpecimenLabel(ILabel):
    """
    A Specimen Label
    """
    
    pretty_specimen_type = zope.schema.Choice(
        title=_(u"Specimen Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_type")
        ) 

class IAliquotLabel(ILabel):
    """
    A Specimen Label
    """
    
    pretty_aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type")
        ) 

