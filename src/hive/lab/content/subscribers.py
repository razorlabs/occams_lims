
from hive.lab.interfaces import IClinicalLab
from hive.lab.interfaces import IResearchLab

from five import grok
from zope.lifecycleevent import IObjectAddedEvent
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
from hive.lab import MessageFactory as _

    
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
