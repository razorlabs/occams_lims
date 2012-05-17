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

from occams.lab.traversal import SpecimenTraverse
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
