from five import grok
from zope.app.intid.interfaces import IIntIds
from zope.lifecycleevent import IObjectAddedEvent
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
import zope.component


from hive.lab.interfaces.specimen import IRequestedSpecimen
from hive.lab.interfaces.labels import ILabelSheet
from hive.lab import MessageFactory as _

    
@grok.subscribe(ILabelSheet, IObjectAddedEvent)
def handleLabelSheetAdded(sheet, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site.
    """
    manage_addZCatalog(sheet, 'labels', u'Labels', REQUEST=None)
    zcat = sheet._getOb('labels')
    label_catalog = zcat._catalog
    for field in ['patient_title', 'study_title', 'protocol_title', 'pretty_specimen_type']:
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)
    dateindex = DateIndex('date_collected')
    label_catalog.addIndex('date_collected', dateindex)  
    label_catalog.addColumn('date_collected')



@grok.subscribe(IRequestedSpecimen, IObjectAddedEvent)
def handleRequestedSpecimenAdded(visit, event):
    """
    When a visit is added, automatically add the requested specimen
    """
    intids = zope.component.getUtility(IIntIds)
    patient = visit.aq_parent
    patient_zid = intids.getId(patient)    
    
    for cycle_relation in visit.cycles:
        cycle_zid = cycle_relation.to_id
        cycle = cycle_relation.to_object
        
        if cycle.related_specimen is not None and len(cycle.related_specimen):
            for specimen_relation in cycle.related_specimen:
                specimenBlueprint = specimen_relation.to_object
                specimenBlueprint.createSpecimen(patient_zid, cycle_zid, visit.visit_date)
                

                #We don't want duplicate specimen
                
#                 foundSpecimen = False
# 
#                 for spec in visit.requestedSpecimen():
#                     if newSpecimen.specimen_type == spec.specimen_type \
#                     and spec.protocol_zid == protocol_zid:
#                 foundSpecimen = True
  

