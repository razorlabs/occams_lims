from AccessControl import getSecurityManager
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from five import grok
from z3c.saconfig import named_scoped_session
from zope.app.intid.interfaces import IIntIds
from zope.lifecycleevent import IObjectAddedEvent
import zope.component
from OFS.interfaces import IObjectWillBeRemovedEvent

from avrc.aeh.interfaces import IVisit
from avrc.aeh.interfaces import IClinicalMarker

from hive.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
from hive.lab.interfaces.labels import ILabel, \
                                       ILabelSheet
from hive.lab.interfaces.managers import ISpecimenManager
from hive.lab.interfaces.specimen import IRequestedSpecimen
from hive.lab import Logger as log



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

    # The behavior will not inject the property if it is created through
    # Python via createContent, so we must double check here so that
    # an AttributeError is not raised.
    check = 'require_specimen'
    if getattr(visit, check, IRequestedSpecimen[check].default):
        user = getSecurityManager().getUser().getId()
        intids = zope.component.getUtility(IIntIds)
        patient = visit.aq_parent
        patient_zid = intids.getId(patient)
        datastore = IDataStore(named_scoped_session(SCOPED_SESSION_KEY))
        specimen_manager = ISpecimenManager(datastore)

        for cycle_relation in visit.cycles:
            cycle_zid = cycle_relation.to_id
            cycle = cycle_relation.to_object

            if cycle.related_specimen is not None and len(cycle.related_specimen):
                for specimen_relation in cycle.related_specimen:
                    specimenBlueprint = specimen_relation.to_object
                    specimen = specimenBlueprint.createSpecimen(patient_zid, cycle_zid, visit.visit_date)
                    specimen_manager.put(specimen)

#                # TODO: make specimen includer for add cycle to visit
#                # We don't want duplicate specimen
#
#                 foundSpecimen = False
#
#                 for spec in visit.requestedSpecimen():
#                     if newSpecimen.specimen_type == spec.specimen_type \
#                     and spec.protocol_zid == protocol_zid:
#                 foundSpecimen = True

@grok.subscribe(IVisit, IObjectWillBeRemovedEvent)
def handleVisitRemoved(item, event):
    """ Retires samples when a Patient is about to removed from
        the Plone content tree.

        TODO: It's still unclear how this exactly is going to work, as it would
        be nice to mark the specimen as destroyed. But this highly depends
        on the workflow (lab technitians ACTUALLY destroying the samples).
        Should an error occurr in the future, this would probably be the
        starting point.
    """
    zid = IClinicalMarker(item).zid

