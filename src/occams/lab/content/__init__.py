from occams.lab.content.adapters import *
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
        return self._data