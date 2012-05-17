"""
Clinical content traversers to transient contexts
"""
from five import grok
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.http import IHTTPRequest

from occams.form.traversal import ExtendedTraversal
from z3c.saconfig import named_scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from occams.lab import model
from occams.lab import interfaces
from occams.lab import SCOPED_SESSION_KEY
from occams.lab.content import SpecimenContext
from occams.lab.content import AliquotContext

@grok.adapter(interfaces.IClinicalLab, IHTTPRequest)
@grok.implementer(IBrowserPublisher)
class SpecimenTraverse(ExtendedTraversal):
    """
    Allows traversal from IClinicalObjects to EAV data forms
    """
    def traverse(self, name):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = session.query(model.SpecimenType).filter(model.SpecimenType.name == name)
        try:
            item = query.one()
            return SpecimenContext(item=item, data=None)
        except NoResultFound:
            return None
        except MultipleResultsFound:
            ## This will be
            raise Exception("There are multiple entries for this specimen type. This is not supported at this time")
        return None


@grok.adapter(interfaces.ISpecimenContext, IHTTPRequest)
@grok.implementer(IBrowserPublisher)
class AliquotTraverse(ExtendedTraversal):
    """
    Allows traversal from IClinicalObjects to EAV data forms
    """
    def traverse(self, name):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        specimen = self.context.item
        query = (
            session.query(model.AliquotType)
            .filter(model.AliquotType.specimen_type == specimen)
            .filter(model.AliquotType.name == name)
        )
        try:
            item = query.one()
            return AliquotContext(item=item, data=None)
        except NoResultFound:
            return None
        except MultipleResultsFound:
            ## This will be
            raise Exception("There are multiple entries for this specimen type. This is not supported at this time")
        return None
