from zope import component
from zope.app.intid.interfaces import IIntIds
from zope.component import getSiteManager
from zope.site.hooks import getSite
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from lovely.session.memcached import MemCachedSessionDataContainer

from plone.memoize import ram

from z3c.saconfig import named_scoped_session
from five import grok

from avrc.data.store import model
from avrc.data.store.interfaces import IDatastore

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
    site = getSite()
    sm = getSiteManager(site)
    ds = sm.queryUtility(IDatastore, 'fia')
    specimen_manager = ds.getSpecimenManager()
    return specimen_manager.get(zid)

@ram.cache(_render_details_cachekey)
def get_patient_initials(zid):
    intids = component.getUtility(IIntIds)
    patient =  intids.queryObject(zid, None)
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
    return session_manager[str(request['__ac']) + str(context)]
    