from Products.CMFCore.utils import getToolByName
from avrc.data.store.interfaces import IDataStore
from hive.lab import SCOPED_SESSION_KEY
from hive.lab.interfaces.managers import ISpecimenManager
from lovely.session.memcached import MemCachedSessionDataContainer
from plone.memoize import ram
from z3c.saconfig import named_scoped_session
from zope import component
from zope.app.intid.interfaces import IIntIds

# ------------------------------------------------------------------------------
# Utilities to cache patient data for specimen and aliquot
# ------------------------------------------------------------------------------
#
def _render_details_cachekey(method, zid):
    return zid

@ram.cache(_render_details_cachekey)
def get_patient_legacy_number(zid):
    intids = component.getUtility(IIntIds)
    patient = intids.queryObject(zid, None)
    if patient:
        if patient.aeh_number is not None:
            return unicode(patient.aeh_number)
        else:
            return u''
    else:
        return None

@ram.cache(_render_details_cachekey)
def get_patient_master_book_number(zid):
    intids = component.getUtility(IIntIds)
    patient = intids.queryObject(zid, None)
    if patient:
        if patient.master_book_number is not None:
            return unicode(patient.master_book_number)
        else:
            return u''
    else:
        return None

@ram.cache(_render_details_cachekey)
def get_patient_title(zid):
    intids = component.getUtility(IIntIds)
    patient = intids.queryObject(zid, None)
    if patient:
        return unicode(patient.getId())
    else:
        return None

@ram.cache(_render_details_cachekey)
def get_study_title(zid):
    intids = component.getUtility(IIntIds)
    protocol = intids.queryObject(zid, None)
    if protocol:
        return unicode(protocol.aq_parent.printabletitle)
    else:
        return None

@ram.cache(_render_details_cachekey)
def get_protocol_title(zid):
    intids = component.getUtility(IIntIds)
    protocol = intids.queryObject(zid, None)
    if protocol:
        if protocol.week is not None:
            return unicode(protocol.week)
        else:
            return u"N/A"
    else:
        return None

@ram.cache(_render_details_cachekey)
def get_specimen(zid):
    specimen_manager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
    return specimen_manager.get(zid)

@ram.cache(_render_details_cachekey)
def get_patient_initials(zid):
    intids = component.getUtility(IIntIds)
    patient = intids.queryObject(zid, None)
    if patient:
        return unicode(patient.initials)
    else:
        return None



def getSession(context, request):
    """
    """
    session_manager = MemCachedSessionDataContainer()
    session_manager.cacheName = u'hive.lab.session'
    session_manager.__name__ = 'session_manager'
    if request.has_key('__ac'):
        ## This will happen in the majority of cases
        sessionkey = str(request['__ac'])
    elif request.has_key('_auth'):
        # If logged in as a zope user, this shows
        sessionkey = str(request('_auth'))
    else:
        # Should probably not do this.
        sessionkey = 'none'
    return session_manager[sessionkey]


## TODO: Move this to aeh
def getPatientForFilter(context, pid):
    """
    given some property of a patient, find the resulting 
    """
    catalog = getToolByName(context, 'portal_catalog')
    intids = component.getUtility(IIntIds)

    results = catalog(portal_type='avrc.aeh.patient',
                                  getId=pid)
    if results and len(results):
        return intids.getId(results[0].getObject())

    results = catalog(portal_type='avrc.aeh.patient',
                                  aeh_number=pid)
    if results and len(results):
        return intids.getId(results[0].getObject())

    results = catalog(portal_type='avrc.aeh.patient',
                                  master_book_number=pid)
    if results and len(results):
        return intids.getId(results[0].getObject())

    return None

