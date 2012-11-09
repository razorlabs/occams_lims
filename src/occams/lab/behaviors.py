import zope.component
import zope.interface
from five import grok
from rwproperty import getproperty, setproperty
from zope.lifecycleevent import IObjectAddedEvent

from avrc.aeh import interfaces as clinical
from occams.lab import interfaces
from occams.lab import model
from occams.lab import Session


class LabLocation(object):
    __doc__ = interfaces.ILabLocation.__doc__

    zope.interface.implements(interfaces.ILabLocation)
    zope.component.adapts(clinical.ISite)

    def __init__(self, context):
        self.context = context

    @getproperty
    def lab_location(self):
        try:
            modelObj = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
            return modelObj.lab_location
        except KeyError:
            return self.context._v_addArgs.get('lab_location')

    @setproperty
    def lab_location(self, value):
        try:
            modelObj = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
            modelObj.lab_location = value
            Session.flush()
        except KeyError:
            # The zid is not set. annotate the object for now
            self.context._v_addArgs['lab_location'] = value


class AvailableSpecimen(object):
    __doc__ = interfaces.IAvailableSpecimen.__doc__

    zope.interface.implements(interfaces.IAvailableSpecimen)
    zope.component.adapts(clinical.IStudy)

    def __init__(self, context):
        self.context = context

    @getproperty
    def specimen_types(self):
        if getattr(self.context, 'zid', None) is not None:
            query = (
                Session.query(model.SpecimenType)
                .join(model.SpecimenType.studies)
                .filter(model.Study.zid == self.context.zid)
                )
            return query.all()
        return self.context._v_addArgs.get('specimen_types')

    @setproperty
    def specimen_types(self, value):
        if value is None:
            value = ()
        try:
            modelObj = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
            modelObj.specimen_types = set(value)
            Session.flush()
        except KeyError:
            # The zid is not set. annotate the object for now
            self.context._v_addArgs['specimen_types'] = set(value)

class RequiredSpecimen(object):
    """
    """
    zope.interface.implements(interfaces.IAvailableSpecimen)
    zope.component.adapts(clinical.ICycle)

    def __init__(self, context):
        self.context = context

    @getproperty
    def specimen_types(self):
        if getattr(self.context, 'zid', None) is not None:
            query = (
                Session.query(model.SpecimenType)
                .join(model.SpecimenType.cycles)
                .filter(model.Cycle.zid == self.context.zid)
                )
            return query.all()
        return self.context._v_addArgs.get('specimen_types')

    @setproperty
    def specimen_types(self, value):
        if value is None:
            value = ()
        try:
            modelObj = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
            modelObj.specimen_types = set(value)
            Session.flush()
        except KeyError:
            # The zid is not set. annotate the object for now
            self.context._v_addArgs['specimen_types'] = set(value)

@grok.subscribe(interfaces.IRequestedSpecimen, IObjectAddedEvent)
def handleRequestedSpecimenAdded(visit, event):
    """
    When a visit is added, automatically add the requested specimen
    """
    # The behavior will not inject the property if it is created through
    # Python via createContent, so we must double check here so that
    # an AttributeError is not raised.
    check = 'require_specimen'
    if getattr(visit, check, interfaces.IRequestedSpecimen[check].default):
        visit_entity = zope.component.getMultiAdapter((visit, Session), clinical.IClinicalModel)
        drawstate = Session.query(model.SpecimenState).filter_by(name=u'pending-draw').one()
        for cycle in visit.cycles:
            for specimen_type in cycle.specimen_types:
                newSpecimen = model.Specimen(
                        patient = visit_entity.patient,
                        cycle = cycle,
                        specimen_type = specimen_type,
                        state=drawstate,
                        collect_date = visit.visit_date,
                        location_id = specimen_type.location_id,
                        tubes = specimen_type.default_tubes
                    )
                Session.add(newSpecimen)
        Session.flush()









