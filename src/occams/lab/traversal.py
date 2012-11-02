"""
Clinical content traversers to transient contexts
"""
from five import grok
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.http import IHTTPRequest

from occams.form.traversal import ExtendedTraversal
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from occams.lab import model
from occams.lab import interfaces
from occams.lab import Session
from occams.lab import content

@grok.adapter(interfaces.IResearchLab, IHTTPRequest)
@grok.implementer(IBrowserPublisher)
class SpecimenTraverse(ExtendedTraversal):
    """
    Allows traversal from IClinicalObjects to EAV data forms
    """
    def traverse(self, name):
        query = Session.query(model.SpecimenType).filter(model.SpecimenType.name == name)
        try:
            item = query.one()
            return content.SpecimenContext(item=item, data=None)
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
        specimen = self.context.item
        query = (
            Session.query(model.AliquotType)
            .filter(model.AliquotType.specimen_type == specimen)
            .filter(model.AliquotType.name == name)
        )
        try:
            item = query.one()
            return content.AliquotContext(item=item, data=None)
        except NoResultFound:
            return None
        except MultipleResultsFound:
            ## This will be
            raise Exception("There are multiple entries for this specimen type. This is not supported at this time")
        return None
