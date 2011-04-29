from hive.lab.interfaces import IViewableAliquot
from hive.lab.interfaces import IViewableSpecimen
from hive.lab.interfaces import IClinicalLab
from hive.lab.interfaces import IResearchLab
from hive.lab.interfaces import ISpecimenLabel

from avrc.data.store.interfaces import IAliquot
from five import grok
from zope.lifecycleevent import IObjectAddedEvent
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
from hive.lab import MessageFactory as _
from avrc.data.store.interfaces import ISpecimen
from hive.lab import utilities as utils

    
@grok.subscribe(IClinicalLab, IObjectAddedEvent)
def handleClinicalLabAdded(lab, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site.
    """
    manage_addZCatalog(lab, 'labels', u'Labels', REQUEST=None)
    zcat = lab._getOb('labels')
    label_catalog = zcat._catalog
    for field in ['patient_title', 'study_title', 'protocol_title', 'pretty_specimen_type']:
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)
    dateindex = DateIndex('date_collected')
    label_catalog.addIndex('date_collected', dateindex)  
    label_catalog.addColumn('date_collected')
    
    
@grok.subscribe(IResearchLab, IObjectAddedEvent)
def handleResearchLabAdded(lab, event):
    """ Research Lab added event handler.
        This method will be triggered when an Research Lab is added to the
        current Site.
    """
    manage_addZCatalog(lab, 'labels', u'Labels', REQUEST=None)
    zcat = lab._getOb('labels')
    label_catalog = zcat._catalog
    for field in ['id','patient_title', 'study_title', 'protocol_title', 'pretty_aliquot_type']:
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)
    dateindex = DateIndex('date_collected')
    label_catalog.addIndex('date_collected', dateindex)  
    label_catalog.addColumn('date_collected')


class ViewableSpecimen(grok.Adapter):
    grok.context(ISpecimen)
    grok.provides(IViewableSpecimen)
        
    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)
        
    @property
    def patient_initials(self):
        return utils.get_patient_initials(self.context.subject_zid)

    @property
    def patient_legacy_number(self):
        return utils.get_patient_legacy_number(self.context.subject_zid)
        
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
    def pretty_tube_type(self):
        return self.context.tube_type
 

class ViewableAliquot(grok.Adapter):
    grok.context(IAliquot)
    grok.provides(IViewableAliquot)
        
    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)
        
    @property
    def patient_initials(self):
        return utils.get_patient_initials(self.context.subject_zid)

    @property
    def patient_legacy_number(self):
        return utils.get_patient_legacy_number(self.context.subject_zid)
        
    @property
    def study_title(self):
        return utils.get_study_title(self.context.protocol_zid)
    
    @property
    def protocol_title(self):
        return utils.get_protocol_title(self.context.protocol_zid)
    
    @property
    def pretty_aliquot_type(self):
        return self.context.aliquot_type
        
        
        
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