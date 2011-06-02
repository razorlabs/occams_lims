from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from avrc.data.store.interfaces import IDatastore
from five import grok
from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel,\
                                       ILabelSheet
from hive.lab.interfaces.managers import ISpecimenManager
from hive.lab.interfaces.specimen import IRequestedSpecimen
from zope.app.intid.interfaces import IIntIds
from zope.lifecycleevent import IObjectAddedEvent
import zope.component

@grok.subscribe(ILabelSheet, IObjectAddedEvent)
def handleLabelSheetAdded(sheet, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site.
    """
    manage_addZCatalog(sheet, 'labels', u'Labels', REQUEST=None)
    zcat = sheet._getOb('labels')
    label_catalog = zcat._catalog
    for field in ILabel.names():
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)


@grok.subscribe(IRequestedSpecimen, IObjectAddedEvent)
def handleRequestedSpecimenAdded(visit, event):
    """
    When a visit is added, automatically add the requested specimen
    """
    intids = zope.component.getUtility(IIntIds)
    patient = visit.aq_parent
    patient_zid = intids.getId(patient)
    sm = zope.component.getSiteManager(visit)
    ds = sm.queryUtility(IDatastore, 'fia')
    specimen_manager = ISpecimenManager(ds)

    for cycle_relation in visit.cycles:
        cycle_zid = cycle_relation.to_id
        cycle = cycle_relation.to_object

        if cycle.related_specimen is not None and len(cycle.related_specimen):
            for specimen_relation in cycle.related_specimen:
                specimenBlueprint = specimen_relation.to_object
                specimen = specimenBlueprint.createSpecimen(patient_zid, cycle_zid, visit.visit_date)
                specimen_manager.put(specimen)

## TODO: make specimen includer for add cycle to visit
                #We don't want duplicate specimen

#                 foundSpecimen = False
# 
#                 for spec in visit.requestedSpecimen():
#                     if newSpecimen.specimen_type == spec.specimen_type \
#                     and spec.protocol_zid == protocol_zid:
#                 foundSpecimen = True


