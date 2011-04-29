from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plone.memoize.instance import memoize

from five import grok

from avrc.aeh.specimen import specimen

specimen_type_list = [
    specimen.ACD,
    specimen.AnalSwab,
    specimen.CSF,
    specimen.GenitalSecretions,
    specimen.Serum,
    specimen.RSGut,
    specimen.TIGut,
    ]

specimen_type_dict = {
    'acd':specimen.ACD,
    'swab':specimen.AnalSwab,
    'csf':specimen.CSF,
    'genital-secretion':specimen.GenitalSecretions,
    'serum':specimen.Serum,
    'rs-gut':specimen.RSGut,
    'ti-gut':specimen.TIGut,
    }
# ------------------------------------------------------------------------------
# Cycle Vocabularys
# ------------------------------------------------------------------------------


class SpecimenVocabulary(object):
    """
    Context source binder to provide a vocabulary of users in a given group.
    """

    grok.implements(IContextSourceBinder)

    @memoize
    def getTerms(self, context=None):
        termlist = []
        for specimen_type in specimen_type_list:
            termlist.append(SimpleTerm(
               title=specimen_type.__name__,
               token=specimen_type.__name__,
               value=specimen_type
               ))
        return termlist

    def getTerm(self, value=None):
        return SimpleTerm(
               title=value.__name__,
               token=value.__name__,
               value=value)

    def __call__(self, context):
        return SimpleVocabulary(terms=self.getTerms())

class StudySpecimenVocabulary(object):
    """
    Context source binder to provide a vocabulary of users in a given group.
    """
    grok.implements(IContextSourceBinder)

    def __init__(self):
        self.property = 'available_specimen'
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
            terms.append(SimpleTerm(
               title=specimen_type.__name__,
               token=specimen_type.__name__,
               value=specimen_type))

        return terms

    def __call__(self, context):

        return SimpleVocabulary(terms=self.getTerms(context))
