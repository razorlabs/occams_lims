import unittest2 as unittest
# from hive.lab import interfaces
# from Acquisition import aq_inner
from hive.lab.testing import OCCAMS_LAB_INTEGRATION_TESTING
# from hive.lab.testing import OCCAMS_LAB_FUNCTIONAL_TESTING
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

from hive.lab import interfaces
from datetime import datetime
from datetime import date
from hive.lab import SCOPED_SESSION_KEY
from z3c.saconfig import named_scoped_session
from zope.component import createObject
from zope.component import queryUtility

from plone.dexterity.interfaces import IDexterityFTI
from Products.CMFCore.utils import getToolByName
from hive.lab import model

from hive.lab.traversal import SpecimenTraverse
from hive.lab.traversal import AliquotTraverse

class TestContentTypesInstalled(unittest.TestCase):
    """
    Checks that the content types can be installed
    """

    layer = OCCAMS_LAB_INTEGRATION_TESTING

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
        institute1.invokeFactory('hive.lab.cliniclab', 'lab1')
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

    def testTraverseToAliquot(self):
        portal = self.layer['portal']
        session = named_scoped_session(SCOPED_SESSION_KEY)
        request = TestRequest()

        # Don't test permissions at this point
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('avrc.aeh.institute', 'institute')
        institute1 = portal['institute']
        institute1.invokeFactory('hive.lab.cliniclab', 'lab1')
        lab1 = institute1['lab1']
        specimentraverser = SpecimenTraverse(lab1, request)
        specimen_type = model.SpecimenType(
            name="specimen1",
             title=u"Some Specimen Type",
             tube_type=u"A Tube that will hold it",
             )
        session.add(specimen_type)
        session.flush()
        specimencontext = specimentraverser.traverse(specimen_type.name)
        aliquot_type = model.AliquotType(
            name="aliquot1",
             title=u"Some Aliquot Type",
             specimen_type=specimen_type,
             )
        aliquotTraverser = AliquotTraverse(specimencontext, request)
        context = aliquotTraverser.traverse(aliquot_type.name)
        self.assertEquals(aliquot_type, context.item)




