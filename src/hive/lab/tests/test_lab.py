import unittest2 as unittest
from hive.lab.testing import OCCAMS_LAB_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName

class TestSetup(unittest.TestCase):
    
    layer = OCCAMS_LAB_INTEGRATION_TESTING

    def test_appointments_installed(self):
        portal = self.layer['portal']
        quickinstaller = getToolByName(portal, 'portal_quickinstaller')
        self.assertTrue(quickinstaller.isProductInstalled('hive.lab'))
