from five import grok
from occams.lab import SCOPED_SESSION_KEY
# from occams.lab.interfaces.managers import ISpecimenManager
from z3c.saconfig import named_scoped_session
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from occams.lab import model
from plone.memoize import ram
from plone.memoize import view
from occams.form.traversal import closest
from avrc.aeh.interfaces import IStudy


# def _render_vocab_cachekey(method, self, context):
#     return "%s_%s" %(str(self.__class__), str(self._modelKlass))

# def _render_specimen_vocab_cachekey(method, self, context):
#     return str(closest(context, IStudy).getId())

class OccamsVocabulary(object):
    grok.implements(IVocabularyFactory)

    @property
    def _modelKlass(self):
        raise NotImplementedError

    def getTerms(self, context):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = (
            session.query(self._modelKlass)
            .order_by(self._modelKlass.title.asc())
            )
        terms=[]
        for term in iter(query):
            terms.append(
                SimpleTerm(
                    title=term.title,
                    token=str(term.name),
                    value=term)
                )
        return terms

    def __call__(self, context):
        return SimpleVocabulary(terms=self.getTerms(context))

class SpecimenStateVocabulary(OccamsVocabulary):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.SpecimenState

grok.global_utility(SpecimenStateVocabulary, name=u"occams.lab.specimenstatevocabulary")

class AliquotStateVocabulary(OccamsVocabulary):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.AliquotState

grok.global_utility(AliquotStateVocabulary, name=u"occams.lab.aliquotstatevocabulary")

class LocationVocabulary(OccamsVocabulary):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.Location

grok.global_utility(LocationVocabulary, name=u"occams.lab.locationvocabulary")

class SpecialInstructionVocabulary(OccamsVocabulary):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.SpecialInstruction

grok.global_utility(SpecialInstructionVocabulary, name=u"occams.lab.specialinstructionvocabulary")


class SpecimenTypeVocabulary(OccamsVocabulary):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.SpecimenType

grok.global_utility(SpecimenTypeVocabulary, name=u"occams.lab.specimentypevocabulary")

class AliquotTypeVocabulary(OccamsVocabulary):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.AliquotType

grok.global_utility(AliquotTypeVocabulary, name=u"occams.lab.aliquottypevocabulary")


class AvailableSpecimenVocabulary(object):
    grok.implements(IVocabularyFactory)

    def getTerms(self, context):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        study = closest(context, IStudy)
        query = (
            session.query(model.SpecimenType)
            .join(model.SpecimenType.studies)
            .filter(model.Study.zid == study.zid)
            .order_by(model.SpecimenType.title.asc())
            )
        terms=[]
        for term in iter(query):
            terms.append(
                SimpleTerm(
                    title=term.title,
                    token=str(term.name),
                    value=term)
                )
        return terms

    def __call__(self, context):
        return SimpleVocabulary(terms=self.getTerms(context))
grok.global_utility(AvailableSpecimenVocabulary, name=u"occams.lab.availablespecimenvocabulary")

