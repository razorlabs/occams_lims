from five import grok
# from occams.lab.interfaces.managers import ISpecimenManager
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from occams.lab import model
from occams.form.traversal import closest
from avrc.aeh.interfaces import IStudy
from occams.lab import Session

class OccamsVocabulary(object):
    grok.implements(IVocabularyFactory)

    @property
    def _modelKlass(self):
        raise NotImplementedError

    def getTerms(self, context):
        query = (
            Session.query(self._modelKlass)
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

    def getTerms(self, context):
        query = (
            Session.query(self._modelKlass)
            .filter_by(active=True)
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
        study = closest(context, IStudy)
        query = (
            Session.query(model.SpecimenType)
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


class LocationStringVocabulary(object):
    grok.implements(IVocabularyFactory)

    _modelKlass=model.Location

    def getTerms(self, context):
        query = (
            Session.query(self._modelKlass)
            .order_by(self._modelKlass.title.asc())
            )
        terms=[]
        for term in iter(query):
            terms.append(
                SimpleTerm(
                    title=term.title,
                    token=str(term.name),
                    value=term.name)
                )
        return terms

    def __call__(self, context):
        return SimpleVocabulary(terms=self.getTerms(context))

grok.global_utility(LocationStringVocabulary, name=u"occams.lab.locationstringvocabulary")
