from datetime import datetime
from datetime import date

from zope import component
from zope import interface
import zope.schema

from five import grok
from hive.lab import MessageFactory as _

from avrc.data.store.interfaces import ISpecimen

from hive.lab import utilities as utils


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
        source=utils.SpecimenAliquotVocabulary(u"specimen_type")
        ) 

class IAliquotLabel(ILabel):
    """
    A Specimen Label
    """
    
    pretty_aliquot_type = zope.schema.Choice(
        title=_(u"Aliquot Type"),
        source=utils.SpecimenAliquotVocabulary(u"aliquot_type")
        ) 

class LabeledSpecimen(grok.Adapter):
    grok.context(ISpecimen)
    grok.provides(ISpecimenLabel)

    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)

    @property
    def study_title(self):
        return utils.get_study_title(self.context.protocol_zid)
    
    @property
    def protocol_title(self):
        return utils.get_protocol_title(self.context.protocol_zid)
        
    @property
    def pretty_specimen_type(self):
        return self.context.specimen_type

    @property
    def date_collected(self):
        return self.context.date_collected