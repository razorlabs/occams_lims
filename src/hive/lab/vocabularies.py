from avrc.data.store.interfaces import IDataStore
from five import grok
from hive.lab import SCOPED_SESSION_KEY
from hive.lab.interfaces.managers import ISpecimenManager
from z3c.saconfig import named_scoped_session
from zope import component
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm, \
                                   SimpleVocabulary


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
        for type in childlist:
            specimen_blueprint = type.to_object
            terms.append(SimpleTerm(
               title=specimen_blueprint.title,
               token=type.to_path,
               value=type))

        return terms

    def __call__(self, context):

        return SimpleVocabulary(terms=self.getTerms(context))


class SpecimenVisitVocabulary(object):
    """
    Context source binder to provide a vocabulary of users in a given group.
    """
    grok.implements(IContextSourceBinder)

    def __init__(self):
        self.property = 'related_specimen'
        self.study = None

    def cycleVocabulary(self):
        context = self.context.aq_inner
        cycles = context.getCycles()
        termlist = []
        intids = component.getUtility(IIntIds)
        for cycle in cycles:
            int
            studytitle = cycle.aq_parent.Title()
            cycletitle = '%s, %s' % (studytitle, cycle.Title())
            protocol_zid = intids.getId(cycle)
            termlist.append(SimpleTerm(
                                       title=cycletitle,
                                       token='%s' % protocol_zid,
                                       value=protocol_zid))
        return SimpleVocabulary(terms=termlist)

class SpecimenAliquotVocabulary(object):
    """ Parameterized-vocabulary for retrieving data store vocabulary terms. """
    grok.implements(IContextSourceBinder)

    def __init__(self, vocabulary_name):
        self.vocabulary_name = unicode(vocabulary_name)

    def __call__(self, context):
        vocab = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY))).get_vocabulary(self.vocabulary_name)
        return vocab

