from zope import interface
import zope.schema
from plone.directives import form
from zope.lifecycleevent import IObjectAddedEvent
from hive.lab import MessageFactory as _
from five import grok
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex

class ILab(form.Schema):
    """
    An Interface for the Labs
    """
    
class IClinicalLab(ILab):
    """
    An Interface for the Labs
    """

class IResearchLab(ILab):
    """
    An Interface for the Labs
    """


@grok.subscribe(IClinicalLab, IObjectAddedEvent)
def handleClinicalLabAdded(lab, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site. It will then begin to pre-populate the Datastore with
        the necessary forms it needs to operate.
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