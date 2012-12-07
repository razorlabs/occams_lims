"""
Data entry functionality
"""
from five import grok
from zope.interface import implements
from occams.form import traversal
from zope.interface.common.mapping import IFullMapping
from sqlalchemy.orm import object_session

from occams.lab import interfaces
from occams.lab import model
from plone.memoize import ram
from avrc.aeh import interfaces as clinical


class SpecimenContext(traversal.DataBaseItemContext):
    """
    Specimen context for traversal. Provides the parts necessary for interacting with
    avrc.data.store Entities in a traversable manner within the Plone context
    """
    implements(interfaces.ISpecimenContext)

    def __init__(self, item, data=None):
        self.item = item
        self.session = object_session(item)

        self.id = None
        self.name = self.__name__ = str(self.item.name)
        title = self.item.title

        self.title = title
        self.Title = lambda:title
        self.description = self.item.description

    @property
    def data(self):
        mapping = getattr(self, '_data', None)
        if mapping is None:
            mapping = IFullMapping(self.item)
            mapping['collect_date'] = self.item.collect_date
            self._data = mapping
        return self._data

class AliquotContext(traversal.DataBaseItemContext):
    """
    Specimen context for traversal. Provides the parts necessary for interacting with
    avrc.data.store Entities in a traversable manner within the Plone context
    """
    implements(interfaces.IAliquotContext)

    def __init__(self, item, data=None):
        self.item = item
        self.session = object_session(item)

        self.id = None
        self.name = self.__name__ = str(self.item.name)
        title = self.item.title

        self.title = title
        self.Title = lambda:title
        self.description = self.item.description

    @property
    def data(self):
        mapping = getattr(self, '_data', None)
        if mapping is None:
            mapping = IFullMapping(self.item)
            mapping['collect_date'] = self.item.collect_date
            self._data = mapping
        return self._data

class ViewableSpecimen(grok.Adapter):
    grok.context(interfaces.ISpecimen)
    grok.provides(interfaces.IViewableSpecimen)

    @property
    def patient_our(self):
        return self.context.patient.our

    @property
    def patient_initials(self):
        return self.context.patient.initials

    @property
    def cycle_title(self):
        return "%s - %s" %(self.context.cycle.study.short_title, self.context.cycle.week)

    @property
    def visit_date(self):
        # this might be slow, but it's the only fix we have available
        session = object_session(self.context)
        visit_query = (
            session.query(model.Visit)
            .filter(model.Visit.patient == self.context.patient)
            .filter(model.Visit.cycles.any(id=self.context.cycle.id))
            )
        visit_entries = visit_query.all()
        if len(visit_entries) == 1:
            return visit_entries[0].visit_date
        return self.context.collect_date

    @property
    def specimen_type_name(self):
        return self.context.specimen_type.name

    @property
    def tube_type(self):
        return self.context.specimen_type.tube_type

class AliquotGenerator(grok.Adapter):
    grok.context(interfaces.IAliquot)
    grok.provides(interfaces.IAliquotGenerator)

    @property
    def count(self):
        return None

def _render_specimen_cachekey(method, self, context):
    return context.specimen_id

def _render_aliquot_type_cachekey(method, self):
    return self.context.aliquot_type_id

class ViewableAliquot(grok.Adapter):
    grok.context(interfaces.IAliquot)
    grok.provides(interfaces.IViewableAliquot)

    @property
    def aliquot_id(self):
        return str(self.context.id)

    @property
    def label_queue(self):
        # Label Queue is dynamically manipulated from the crud form
        # and should not be set here.
        return None

    @property
    def aliquot_type_title(self):
        return self.context.aliquot_type.title

    @property
    def state_title(self):
        return self.context.state.title

    @property
    def patient_our(self):
        return self.getPatientOur(self.context)

    @ram.cache(_render_specimen_cachekey)
    def getPatientOur(self, context):
        return context.specimen.patient.our

    @property
    def patient_legacy_number(self):
        return self.getPatientLegacyNumber(self.context)

    @ram.cache(_render_specimen_cachekey)
    def getPatientLegacyNumber(self, context):
        return context.specimen.patient.legacy_number

    @property
    def cycle_title(self):
        return self.getCycleTitle(self.context)

    @ram.cache(_render_specimen_cachekey)
    def getCycleTitle(self, context):
        return "%s - %s" %(context.specimen.cycle.study.short_title, context.specimen.cycle.week)


    @property
    def location_title(self):
        return self.context.location.title

    ##  For the checkout display
    @property
    def vol_count(self):
        if self.context.volume is not None and self.context.volume > 0:
            ret = self.context.volume
        elif self.context.cell_amount is not None and self.context.cell_amount > 0:
            ret = self.context.cell_amount
        else:
            ret = u'--'
        return ret

    @property
    def frb(self):
        f = '?'
        r = '?'
        b = '?'
        if self.context.freezer is not None:
            f = self.context.freezer
        if self.context.rack is not None:
            r = self.context.rack
        if self.context.box is not None:
            b = self.context.box
        return "%s/%s/%s" % (f, r, b)

    @property
    def thawed_num(self):
        if self.context.thawed_num is None or self.context.thawed_num < 0:
            return 0
        else:
            return self.context.thawed_num


