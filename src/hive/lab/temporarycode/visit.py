
from datetime import date

from zope import component
from zope import interface
from zope import schema
from zope.app.intid.interfaces import IIntIds
from zope.component import getSiteManager
from zope.component import getUtility
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.schema.vocabulary import SimpleVocabulary

from five import grok
from plone.memoize import volatile

from plone.app.content.interfaces import INameFromTitle
from plone.dexterity import content
from plone.directives import form
from plone.formwidget.contenttree import ObjPathSourceBinder

from z3c.relationfield.relation import RelationValue
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList

from avrc.aeh import MessageFactory as _
from avrc.aeh.content import cycle
from avrc.aeh.specimen import specimen
from avrc.aeh.specimen.specimen import ISpecimen
from avrc.aeh.vocabularies import FormsVocabulary

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISpecimen as IDSSpecimen
from avrc.data.store.interfaces import IVisit as IDSVisit
from avrc.data.store.clinical import Visit as DSVisit

from plone.formwidget.autocomplete import AutocompleteMultiFieldWidget


DISPLAY_STATES = [u'complete', u'not-done']
# ------------------------------------------------------------------------------
# Plone Content Schemas
# ------------------------------------------------------------------------------
def _visit_datastore_cache_key(method, self, klass, state):

    return self.modified()

class IVisit(form.Schema):
    """ An enrollment of a patient in a study """

    visit_date = schema.Date(
                          title=_(u'Visit Date'),
                          description=_(u'The date of this visit'),
                          )



    form.widget(cycles=AutocompleteMultiFieldWidget)
    cycles = RelationList(
                          title=_(u'Cycles'),
                          description=_(u'The Cycles for this Visit.'),
                          value_type=RelationChoice(
                                source=ObjPathSourceBinder(
                                object_provides=(cycle.ICycleMarker.__identifier__)
                                )
                            ),
                          )


    def requested_specimen():
        """ """

    def requestedSpecimen():
        """ """

    def addRequestedSpecimen():
        """ """

    def getCycles():
        """ Get the list of cycles that should be covered by this visit """

    def getBehaviorFormList():
        """ Get the list of required behavior forms """

    def getOptionalBehaviorFormList():
        """ Get the remaining behaviors from the enrolled studies """

    def getTestFormList():
        """ get the list of tests for this visit """

    def getOptionalTestFormVocabulary():
        """ get the list of remaining tests that can be requested """

    def getSpecimenFormList():
        """ get the list of specimens for this visit """

    def getOptionalSpecimenFormVocabulary():
        """ get the list of remaining specimens that can be requested """

class Visit(content.Item):
    interface.implements(IVisit)

    __doc__ = IVisit.__doc__

    @property
    def title(self):
        """Dexterity's Dublin Core implementation requires this"""
        return 'Visit %s' % (self.visit_date)

    @title.setter
    def title(self, value):
        """Dexterity's Dublin Core implementation requires this"""

    @property
    def requested_specimen(self):
        return self.requestedSpecimen()

    def requestedSpecimen(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimenlist = []
        specimen_manager = ds.specimen
        intids = component.getUtility(IIntIds)
        patient = self.aq_parent
        patient_zid = intids.getId(patient)
        for cycle in self.cycles:
            cycle_zid = cycle.to_id
            kwargs = dict(protocol_zid=cycle_zid, subject_zid=patient_zid)
            for specimenobj in specimen_manager.list_specimen_by_group(**kwargs):
                newSpecimen = ISpecimen(specimenobj)
                specimenlist.append(newSpecimen)
        return specimenlist

    def addRequestedSpecimen(self, iface=None, protocol_zid=None):
        """ """
        intids = component.getUtility(IIntIds)
        patient = self.aq_parent
        patient_zid = intids.getId(patient)

        kwarg = {
            'date_collected': self.visit_date,
            'subject_zid': int(patient_zid),
            'protocol_zid': protocol_zid
            }

        newSpecimen = None

        if iface.isOrExtends(specimen.ACD):
            newSpecimen = specimen.ACDSpecimen(**kwarg)
        elif iface.isOrExtends(specimen.AnalSwab):
            newSpecimen = specimen.AnalSwabSpecimen(**kwarg)
        elif iface.isOrExtends(specimen.CSF):
            newSpecimen = specimen.CSFSpecimen(**kwarg)
        elif iface.isOrExtends(specimen.GenitalSecretions):
            newSpecimen = specimen.GSSpecimen(**kwarg)
        elif iface.isOrExtends(specimen.Serum):
            newSpecimen = specimen.SerumSpecimen(**kwarg)
        elif iface.isOrExtends(specimen.RSGut):
            newSpecimen = specimen.RSGutSpecimen(**kwarg)
        elif iface.isOrExtends(specimen.TIGut):
            newSpecimen = specimen.TIGutSpecimen(**kwarg)
        else:
            raise Exception('Cannot find an object for %s' % iface)

        foundSpecimen = False

        for spec in self.requestedSpecimen():
            if newSpecimen.specimen_type == spec.specimen_type \
                    and spec.protocol_zid == protocol_zid:
                foundSpecimen = True

        if not foundSpecimen:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            ds.specimen.put(IDSSpecimen(newSpecimen))


# ------------------------------------------------------------------------------
# Adapters
# ------------------------------------------------------------------------------

class VisitNameGenerator(grok.Adapter):
    """ Generates the name for a patient by creating an our number for said
        patient.
    """
    grok.context(IVisit)
    grok.provides(INameFromTitle)

    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        return str('Visit %s' % self.context.visit_date)

@grok.adapter(IVisit)
@grok.implementer(IDSVisit)
def VisitToDSVisit(context):
    """ Converts an AEH visit to a data store visit """

    intids = component.getUtility(IIntIds)
    patient = context.aq_parent

    # TODO: use createObject?
    dsvisit_obj = DSVisit()
    dsvisit_obj.zid = intids.getId(context)
    dsvisit_obj.protocol_zids = []
    dsvisit_obj.visit_date = context.visit_date
    dsvisit_obj.subject_zid = intids.getId(patient)

    for cycle in context.getCycles():
        dsvisit_obj.protocol_zids.append(intids.getId(cycle))

    return dsvisit_obj


# ------------------------------------------------------------------------------
# Event Handlers
# ------------------------------------------------------------------------------

@grok.subscribe(IVisit, IObjectAddedEvent)
def handleVisitAdded(visit, event):
    patient = visit.aq_parent
    intids = getUtility(IIntIds)

    ds = getUtility(IDatastore, 'fia', visit)
    schema_manager = ds.schemata
    visit_manager = ds.getVisitManager()
    newobjlist = []
    requested_tests = []
    if visit.cycles is None or not len(visit.cycles):
        cycle_relations = []
        cycleList = patient.getCycleList(visit.visit_date)
        for cycle in cycleList:
            cycleid = intids.getId(cycle)
            cyclerelation = RelationValue(cycleid)
            cycle_relations.append(cyclerelation)
        visit.cycles = cycle_relations
    for cycle in visit.cycles:
        cycleid = cycle.to_id
        cycle = cycle.to_object

        kwarg = {'date_collected': visit.visit_date}

        forms = []
        forms.extend(cycle.required_behavior_forms)
        forms.extend(cycle.required_tests)
        for form in forms:
            if form not in requested_tests:
                requested_tests.append(form)
                iface = schema_manager.get(unicode(form))
                newobj = ds.put(ds.spawn(iface, **kwarg))
                newobj.setState(u'pending-entry')
                newobjlist.append(newobj)

        for iface in cycle.required_specimen:
            visit.addRequestedSpecimen(iface=iface, protocol_zid=int(cycleid))

    obj = visit_manager.put(IDSVisit(visit))

    if len(newobjlist):
        visit_manager.add_instances(obj, newobjlist)

@grok.subscribe(IVisit, IObjectModifiedEvent)
def handleDSVisitModified(visit, event):
    """ Event handler for that should be called when the Visit content type
        is updated. It will then synchronize its data with the data store.
    """

    ds = getUtility(IDatastore, 'fia', visit)
    visit_manager = ds.getVisitManager()
    schema_manager = ds.schemata

    # Contains new forms to be added to the visit
    newobj_list = []

    # Updates done to IVisit
    updates_obj = None

    descriptions = event.descriptions or []

    # We're only interested in IVisit updates
    for description in descriptions:
        if description.interface.isOrExtends(IVisit):
            updates_obj = description
            break
    requested_tests = []
    if updates_obj:
        if 'cycles' in updates_obj.attributes:
            # Inspect each of the (potentially new) cycles added and add their
            # specimen and tests
            for cycle_rel in visit.cycles:
                cycle_obj = cycle_rel.to_object
                kwarg = {'state': 'pending-entry', 'date_collected': visit.visit_date}
                forms = []
                forms.extend(cycle_obj.required_behavior_forms)
                forms.extend(cycle_obj.required_tests)
                for form in forms:
                    if form not in requested_tests:
                        requested_tests.append(form)
#                        iface = schema_manager.get(unicode(form))
                        data_obj = visit_manager.getEnteredDataOfType(IDSVisit(visit), form)
                        if data_obj is None:
                        # Add the test to the AEH and data store object queue
                            iface = schema_manager.get(unicode(form))
                            newobj = ds.put(ds.spawn(iface,
                                state=u'pending-entry',
                                date_collected=visit.visit_date
                                ))
                            newobj_list.append(newobj)

                # Add the specimen to the AEH object (not the data store yet,
                # until they're checked-in)
                for iface in cycle_obj.required_specimen:
                    visit.addRequestedSpecimen(
                        iface=iface,
                        protocol_zid=int(cycle_rel.to_id)
                        )

        # Any other property modification should be picked up within the object
        # itself and, consequently, the adapted data store object
        dsvisit_obj = visit_manager.put(IDSVisit(visit))

        if len(newobj_list):
            visit_manager.add_instances(dsvisit_obj, newobj_list)

# ------------------------------------------------------------------------------
# Default Values
# ------------------------------------------------------------------------------

@form.default_value(field=IVisit['visit_date'])
def startDefaultValue(data):
    return date.today()
