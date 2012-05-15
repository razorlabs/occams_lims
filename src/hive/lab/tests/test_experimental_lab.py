import unittest2 as unittest
# from hive.lab import interfaces
# from Acquisition import aq_inner
from hive.lab.testing import OCCAMS_LAB_INTEGRATION_TESTING
# from hive.lab.testing import OCCAMS_LAB_FUNCTIONAL_TESTING
# from plone.app.testing import TEST_USER_ID
# from plone.app.testing import setRoles
# from plone.app.testing import login

# from zope.component import createObject
# from zope.component import queryUtility

# from plone.dexterity.interfaces import IDexterityFTI

# from plone.app.testing import TEST_USER_NAME


class TestCase(unittest.TestCase):
    """
    """
    layer = OCCAMS_LAB_INTEGRATION_TESTING

    def testFails(self):
        self.assertTrue(False)