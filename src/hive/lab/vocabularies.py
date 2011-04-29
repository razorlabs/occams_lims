from plone.formwidget.contenttree import ObjPathSourceBinder
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plone.memoize.instance import memoize

from five import grok

from avrc.aeh.specimen import specimen


class SpecimenVocabulary(object):
    """
    Context source binder to provide a vocabulary of users in a given group.
    """
    grok.implements(IContextSourceBinder)

    def __init__(self):
        self.property = 'related_specimen'
        self.study = None

#    @memoize
    def getTerms(self, context=None):
        if context.portal_type == 'avrc.aeh.study':
            self.study = context
        elif context.portal_type == 'avrc.aeh.cycle' \
                and getattr(context, "__parent__", None):
            self.study = context.__parent__

        childlist = getattr(self.study, self.property, [])

        terms = []
        for specimen_type in childlist:
            specimen_blueprint = specimen_type.to_object
            terms.append(SimpleTerm(
               title=specimen_blueprint.title,
               token=specimen_type.to_path,
               value=specimen_type))

        return terms

    def __call__(self, context):

        return SimpleVocabulary(terms=self.getTerms(context))
        
        
        
        