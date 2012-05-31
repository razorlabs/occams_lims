import unittest2 as unittest
# from occams.lab import interfaces
# from Acquisition import aq_inner
from occams.lab.testing import OCCAMS_LAB_INTEGRATION_TESTING
# from occams.lab.testing import OCCAMS_LAB_FUNCTIONAL_TESTING
# from plone.app.testing import TEST_USER_ID
# from plone.app.testing import setRoles
# from plone.app.testing import login
from zope.publisher.browser import TestRequest

# from zope.component import createObject
# from zope.component import queryUtility

# from plone.dexterity.interfaces import IDexterityFTI

# from plone.app.testing import TEST_USER_NAME

from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

from occams.lab import interfaces
from datetime import datetime
from datetime import date
from occams.lab import SCOPED_SESSION_KEY
from z3c.saconfig import named_scoped_session
from zope.component import createObject
from zope.component import queryUtility

from plone.dexterity.interfaces import IDexterityFTI
from Products.CMFCore.utils import getToolByName
from occams.lab import model
from occams.lab.browser import clinicallab
from occams.lab.traversal import SpecimenTraverse

from zope.interface import implements
class DummyClinicalLab(object):
    """
    Isolated patient with minimal information needed for tests
    """
    implements(interfaces.IClinicalLab)

class TestContentTypesInstalled(unittest.TestCase):
    """
    Checks that the content types can be installed
    """

    layer = OCCAMS_LAB_INTEGRATION_TESTING

    def testInstalled(self):
        """
        Helper method to check that the content type can be properly installed
        and created.
        """
        name= 'occams.lab.cliniclab'
        portal = self.layer['portal']
        portal_types = getToolByName(portal, 'portal_types')
        self.assertTrue(name in portal_types)

        fti = queryUtility(IDexterityFTI, name=name)
        schema = fti.lookupSchema()
        self.assertNotEquals(None, fti)
        self.assertEquals(interfaces.IClinicalLab, schema)

        factory = fti.factory
        new_object = createObject(factory)
        self.failUnless(interfaces.IClinicalLab.providedBy(new_object))

    def testClinicLabRestricted(self):
        self.fail()

    def testTraverseToSpecimen(self):
        """
        Traverse to a specimen from the clinic lab
        """
        portal = self.layer['portal']
        session = named_scoped_session(SCOPED_SESSION_KEY)
        request = TestRequest()

        # Don't test permissions at this point
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('avrc.aeh.institute', 'institute')
        institute1 = portal['institute']
        institute1.invokeFactory('occams.lab.cliniclab', 'lab1')
        lab1 = institute1['lab1']
        traverser = SpecimenTraverse(lab1, request)

        specimen_type = model.SpecimenType(
            name="specimen1",
             title=u"Some Specimen Type",
             tube_type=u"A Tube that will hold it",
             )
        session.add(specimen_type)
        session.flush()
        context = traverser.traverse(specimen_type.name)
        self.assertEquals(specimen_type, context.item)



class testClinicLabView(unittest.TestCase):
        layer = OCCAMS_LAB_INTEGRATION_TESTING

        def setUp(self):
            self.session = named_scoped_session(SCOPED_SESSION_KEY)
            dummy_specimen_type = model.SpecimenType(
                name="Dummy Specimen Type",
                 title=u"Dummy Specimen Type",
                 tube_type=u"A Tube",
                 )
            self.session.add(dummy_specimen_type)
            self.session.flush()

            for state in ['pending-draw', 'batched', 'postponed', 'complete', 'cancel-draw']:
                specimen_state= model.SpecimenState(
                name=state,
                title=unicode(state)
                )
                self.session.add(specimen_state)
                self.session.flush()
                dummy_specimen = model.Specimen(
                     specimen_type=dummy_specimen_type,
                     patient = self.layer['dummy_patient'],
                     cycle = self.layer['dummy_cycle'],
                     state = specimen_state
                     )
                self.session.add(dummy_specimen)
                self.session.flush()
                # setattr(self, state, dummy_specimen)

        def tearDown(self):
            self.session.rollback()


        def testCurrentUser(self):
            form = clinicallab.ClinicalLabViewForm(DummyClinicalLab(), self.layer['request'])
            self.assertEquals(form.currentUser, TEST_USER_ID )

        def testDisplayState(self):
            form = clinicallab.ClinicalLabViewForm(DummyClinicalLab(), self.layer['request'])
            self.assertIn(u'pending-draw', form.display_state)

        def testItems(self):
            form = clinicallab.ClinicalLabViewForm(DummyClinicalLab(), self.layer['request'])
            items=form.get_items()
            self.assertIsNotNone(items)
            self.assertEqual(1, len(items))
            item = items[0][1]
            self.assertEqual(item.state.name,u'pending-draw')


