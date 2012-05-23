import unittest2 as unittest
from occams.lab import model
from occams.lab.testing import OCCAMS_LAB_INTEGRATION_TESTING

from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IVocabulary

from occams.lab import vocabularies
from z3c.saconfig import named_scoped_session
from occams.lab import SCOPED_SESSION_KEY
from zope.component import getUtility


class fakeContext(object):
    """
    """

class OccamsVocabularyTestCase(unittest.TestCase):
    layer = OCCAMS_LAB_INTEGRATION_TESTING

    def _assertImplements(self, vocabname):
        portal = self.layer['portal']
        factory = getUtility(IVocabularyFactory, name=vocabname)
        vocabulary = factory(portal)
        self.assertTrue(IVocabulary.providedBy(vocabulary))

    def _assertVocab(self, modelKlass, vocabKlass):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        entry = modelKlass(
            name="token",
            title=u"Title")

        session.add(entry)
        session.flush()
        vocabularyFactory = vocabKlass()
        vocabulary = vocabularyFactory(fakeContext)
        self.assertEquals(1, len(vocabulary))
        self.assertTrue('token' in [term.token for term in vocabulary])
        self.assertTrue(1 in [term.value for term in vocabulary])
        self.assertTrue(u'Title' in [term.title for term in vocabulary])

    def testSpecimenStateImplementation(self):
        self._assertImplements("occams.lab.specimenstatevocabulary")

    def testSpecimenStateListVocabItems(self):
        self._assertVocab(model.SpecimenState, vocabularies.SpecimenStateVocabulary)

    def testAliquotStateImplementation(self):
        self._assertImplements("occams.lab.aliquotstatevocabulary")

    def testAliquotStateListVocabItems(self):
        self._assertVocab(model.AliquotState, vocabularies.AliquotStateVocabulary)

    def testLocationImplementation(self):
        self._assertImplements("occams.lab.locationvocabulary")

    def testLocationListVocabItems(self):
        self._assertVocab(model.Location, vocabularies.LocationVocabulary)

    def testSpecialInstructionImplementation(self):
        self._assertImplements("occams.lab.specialinstructionvocabulary")

    def testSpecialInstructionListVocabItems(self):
        self._assertVocab(model.SpecialInstruction, vocabularies.SpecialInstructionVocabulary)

    def testSpecimenTypeImplementation(self):
        self._assertImplements("occams.lab.specimentypevocabulary")

    def testSpecimenTypeListVocabItems(self):
        self._assertVocab(model.SpecimenType, vocabularies.SpecimenTypeVocabulary)

    def testAliquotTypeImplementation(self):
        self._assertImplements("occams.lab.aliquottypevocabulary")

    def testAliquotTypeListVocabItems(self):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        specimentype = model.SpecimenType(
            name='specimentype',
            title=u"",
            )
        session.add(specimentype)
        session.flush()
        entry = model.AliquotType(
            name="token",
            title=u"Title",
            specimen_type=specimentype)

        session.add(entry)
        session.flush()
        vocabularyFactory = vocabularies.AliquotTypeVocabulary()
        vocabulary = vocabularyFactory(fakeContext)
        self.assertEquals(1, len(vocabulary))
        self.assertTrue('token' in [term.token for term in vocabulary])
        self.assertTrue(1 in [term.value for term in vocabulary])
        self.assertTrue(u'Title' in [term.title for term in vocabulary])