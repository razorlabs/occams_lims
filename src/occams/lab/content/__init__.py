# from occams.lab.content.adapters import *
from occams.lab.content.factories import *
from occams.lab.content.subscribers import *

"""
Data entry functionality
"""
from five import grok
from zope.interface import implements
import zope.component
from occams.form import traversal
from zope.interface.common.mapping import IFullMapping
from sqlalchemy.orm import object_session
from occams.form.traversal import closest
from sqlalchemy.orm.exc import NoResultFound
from plone.memoize import ram
import zope.interface

from occams.lab import interfaces

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
        return self._dat

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
        if self.context.study_cycle_label:
            return self.context.study_cycle_label
        return "%s - %s" %(self.context.cycle.study.short_title, self.context.cycle.week)

    @property
    def visit_date(self):
        return self.context.visit.visit_date


    @property
    def specimen_type_name(self):
        return self.context.specimen_type.name

    # @property
    # def state(self):
    #     return self.context.state.name

    @property
    def tube_type(self):
        return self.context.specimen_type.tube_type


class IAliquotGenerator(grok.Adapter):
    grok.context(interfaces.IAliquot)
    grok.provides(interfaces.IAliquotGenerator)

    @property
    def count(self):
        return None

class ViewableAliquot(grok.Adapter):
    grok.context(interfaces.IAliquot)
    grok.provides(interfaces.IViewableAliquot)

    @property
    def patient_our(self):
        return self.context.specimen.patient.our

    @property
    def patient_legacy_number(self):
        return self.context.specimen.patient.legacy_number

    @property
    def cycle_title(self):
        if self.context.specimen.study_cycle_label:
            return self.context.specimen.study_cycle_label
        return "%s - %s" %(self.context.specimen.cycle.study.short_title, self.context.specimen.cycle.week)


    @property
    def aliquot_type_name(self):
        return self.context.aliquot_type.title

    # @property
    # def state(self):
    #     return self.context.state.name
