from Products.CMFCore.utils import getToolByName
from hive.lab import Logger as default_logger

PROFILE_ID = u'profile-hive.lab:default'

def import_(context, logger=default_logger):
    logger.info(u'Reloading types.')
    portal_setup = getToolByName(context, 'portal_setup')
    # Plone uses 'typeinfo' as the profile step and not 'types' like in the
    # xml profile file name, wtf...
    portal_setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    logger.info(u'Upgrade complete')



