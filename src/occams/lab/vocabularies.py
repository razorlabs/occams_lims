from five import grok
from occams.lab import SCOPED_SESSION_KEY
# from occams.lab.interfaces.managers import ISpecimenManager
from z3c.saconfig import named_scoped_session
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from occams.lab import model
from plone.memoize import ram


def _render_vocab_cachekey(method, self, context):
    return str(self._modelKlass)

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

