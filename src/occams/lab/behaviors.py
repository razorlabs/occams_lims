"""
Data entry functionality
"""
from zope.interface import implements
from five import grok

from occams.lab import interfaces
from rwproperty import getproperty, setproperty

from zope.component import adapts

from avrc.aeh.interfaces import IStudy, ICycle
from occams.lab import SCOPED_SESSION_KEY
from z3c.saconfig import named_scoped_session
from occams.lab import model
from sqlalchemy.orm import object_session
from zope.lifecycleevent import IObjectAddedEvent
class AvailableSpecimen(object):
    """
    """
    implements(interfaces.IAvailableSpecimen)
    adapts(IStudy)

    def __init__(self, context):
        self.context = context
    
    @getproperty
    def specimen_types(self):
        if getattr(self.context, 'zid', None) is not None:
            session = named_scoped_session(SCOPED_SESSION_KEY)
            query = (
                session.query(model.SpecimenType)
                .join(model.SpecimenType.studies)
                .filter(model.Study.zid == self.context.zid)
                )
            return query.all()
        return self.context._addArgs.get('specimen_types')

    @setproperty
    def specimen_types(self, value):
        if value is None:
            value = ()
        if getattr(self.context, 'zid', None) is not None:
            modelObj = self.context.getSQLObj()
            session = object_session(modelObj)
            modelObj.specimen_types = set(value)
            session.flush()
        else:
            self.context._addArgs['specimen_types'] = set(value)


class RequiredSpecimen(object):
    """
    """
    implements(interfaces.IAvailableSpecimen)
    adapts(ICycle)

    def __init__(self, context):
        self.context = context
    
    @getproperty
    def specimen_types(self):
        if getattr(self.context, 'zid', None) is not None:
            session = named_scoped_session(SCOPED_SESSION_KEY)
            query = (
                session.query(model.SpecimenType)
                .join(model.SpecimenType.cycles)
                .filter(model.Cycle.zid == self.context.zid)
                )
            return query.all()
        return self.context._addArgs.get('specimen_types')

    @setproperty
    def specimen_types(self, value):
        if value is None:
            value = ()
        if getattr(self.context, 'zid', None) is not None:
            modelObj = self.context.getSQLObj()
            session = object_session(modelObj)
            modelObj.specimen_types = set(value)
            session.flush()
        else:
            self.context._addArgs['specimen_types'] = set(value)

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
        session = named_scoped_session(SCOPED_SESSION_KEY)
        visitSQL = visit.getSQLObj()
        drawstate = session.query(model.SpecimenState).filter_by(name=u'pending-draw').one()
        for cycle in visit.cycles:
            for specimen_type in cycle.specimen_types:
                newSpecimen = model.Specimen(
                        patient = visitSQL.patient,
                        cycle = cycle,
                        specimen_type = specimen_type,
                        state=drawstate,
                        collect_date = visit.visit_date,
                        location_id = specimen_type.location_id,
                        tubes = specimen_type.default_tubes
                    )
                session.add(newSpecimen)
                session.flush()









