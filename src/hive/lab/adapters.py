from hive.lab.interfaces import IViewableAliquot
from hive.lab.interfaces import IViewableSpecimen
from hive.lab.interfaces import IClinicalLab
from hive.lab.interfaces import IResearchLab
from hive.lab.interfaces import ISpecimenLabel

from avrc.data.store.interfaces import IAliquot
from five import grok
from zope.lifecycleevent import IObjectAddedEvent
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
from hive.lab import MessageFactory as _
from avrc.data.store.interfaces import ISpecimen
from hive.lab import utilities as utils

    
@grok.subscribe(IClinicalLab, IObjectAddedEvent)
def handleClinicalLabAdded(lab, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site.
    """
    manage_addZCatalog(lab, 'labels', u'Labels', REQUEST=None)
    zcat = lab._getOb('labels')
    label_catalog = zcat._catalog
    for field in ['patient_title', 'study_title', 'protocol_title', 'pretty_specimen_type']:
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)
    dateindex = DateIndex('date_collected')
    label_catalog.addIndex('date_collected', dateindex)  
    label_catalog.addColumn('date_collected')
    
    
@grok.subscribe(IResearchLab, IObjectAddedEvent)
def handleResearchLabAdded(lab, event):
    """ Research Lab added event handler.
        This method will be triggered when an Research Lab is added to the
        current Site.
    """
    manage_addZCatalog(lab, 'labels', u'Labels', REQUEST=None)
    zcat = lab._getOb('labels')
    label_catalog = zcat._catalog
    for field in ['id','patient_title', 'study_title', 'protocol_title', 'pretty_aliquot_type']:
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)
    dateindex = DateIndex('date_collected')
    label_catalog.addIndex('date_collected', dateindex)  
    label_catalog.addColumn('date_collected')


#### From institute.py
## Should happen on addition of specimen
#from avrc.aeh.specimen._import import datastore_import as specimen_vocabularies

# def addSpecimen(datastore, specimen_vocabulary_map):
#     """ Helper method to add the specimen vocabulary mapping to the Datastore.
# 
#         TODO: migrate to Datastore code base
#     """
#     Session = datastore.getScopedSession()
#     session = Session()
# 
#     for vocabulary_name, vocabulary_obj in specimen_vocabulary_map.items():
#         vocabuylary_name = unicode(vocabulary_name)
# 
#         num_entries = session.query(model.SpecimenAliquotTerm)\
#             .filter_by(vocabulary_name=vocabuylary_name)\
#             .count()
# 
#         # Only enter the specimen vocabulary if it doesn't already exist in
#         # the database
#         if num_entries <= 0:
#             for term_obj in vocabulary_obj:
#                 session.add(model.SpecimenAliquotTerm(
#                     vocabulary_name=vocabulary_name,
#                     title=term_obj.title and unicode(term_obj.title) or None,
#                     token=unicode(term_obj.token),
#                     value=unicode(term_obj.value)
#                     ))
# 
#     session.flush()

## Add handler for cycle

# @grok.subscribe(IVisit, IObjectAddedEvent)
# def handleVisitAdded(visit, event):
#     patient = visit.aq_parent
#     intids = getUtility(IIntIds)
# 
#     ds = getUtility(IDatastore, 'fia', visit)
#     schema_manager = ds.getSchemaManager()
#     visit_manager = ds.getVisitManager()
#     newobjlist = []
#     requested_tests = []
#     if visit.cycles is None or not len(visit.cycles):
#         cycle_relations = []
#         cycleList = patient.getCycleList(visit.visit_date)
#         for cycle in cycleList:
#             cycleid = intids.getId(cycle)
#             cyclerelation = RelationValue(cycleid)
#             cycle_relations.append(cyclerelation)
#         visit.cycles = cycle_relations
#     for cycle in visit.cycles:
#         cycleid = cycle.to_id
#         cycle = cycle.to_object
# 
#         kwarg = {'date_collected': visit.visit_date}
# 
#         forms = []
#         forms.extend(cycle.required_behavior_forms)
#         forms.extend(cycle.required_tests)
#         for form in forms:
#             if form not in requested_tests:
#                 requested_tests.append(form)
#                 iface = schema_manager.get(unicode(form))
#                 newobj = ds.put(ds.spawn(iface, **kwarg))
#                 newobj.setState(u'pending-entry')
#                 newobjlist.append(newobj)
# 
#         for iface in cycle.required_specimen:
#             visit.addRequestedSpecimen(iface=iface, protocol_zid=int(cycleid))
# 
#     obj = visit_manager.put(IDSVisit(visit))
# 
#     if len(newobjlist):
#         visit_manager.add_instances(obj, newobjlist)

### And on modify

#                 for iface in cycle_obj.required_specimen:
#                     visit.addRequestedSpecimen(
#                         iface=iface,
#                         protocol_zid=int(cycle_rel.to_id)
#                         )


##### Specimen handlers for Visits

#     @property
#     def requested_specimen(self):
#         return self.requestedSpecimen()
# 
#     def requestedSpecimen(self):
#         sm = getSiteManager(self)
#         ds = sm.queryUtility(IDatastore, 'fia')
#         specimenlist = []
#         specimen_manager = ds.getSpecimenManager()
#         intids = component.getUtility(IIntIds)
#         patient = self.aq_parent
#         patient_zid = intids.getId(patient)
#         for cycle in self.cycles:
#             cycle_zid = cycle.to_id
#             kwargs = dict(protocol_zid=cycle_zid, subject_zid=patient_zid)
#             for specimenobj in specimen_manager.list_specimen_by_group(**kwargs):
#                 newSpecimen = ISpecimen(specimenobj)
#                 specimenlist.append(newSpecimen)
#         return specimenlist
# 
#     def addRequestedSpecimen(self, iface=None, protocol_zid=None):
#         """ """
#         intids = component.getUtility(IIntIds)
#         patient = self.aq_parent
#         patient_zid = intids.getId(patient)
# 
#         kwarg = {
#             'date_collected': self.visit_date,
#             'subject_zid': int(patient_zid),
#             'protocol_zid': protocol_zid
#             }
# 
#         newSpecimen = None
# 
#         if iface.isOrExtends(specimen.ACD):
#             newSpecimen = specimen.ACDSpecimen(**kwarg)
#         elif iface.isOrExtends(specimen.AnalSwab):
#             newSpecimen = specimen.AnalSwabSpecimen(**kwarg)
#         elif iface.isOrExtends(specimen.CSF):
#             newSpecimen = specimen.CSFSpecimen(**kwarg)
#         elif iface.isOrExtends(specimen.GenitalSecretions):
#             newSpecimen = specimen.GSSpecimen(**kwarg)
#         elif iface.isOrExtends(specimen.Serum):
#             newSpecimen = specimen.SerumSpecimen(**kwarg)
#         elif iface.isOrExtends(specimen.RSGut):
#             newSpecimen = specimen.RSGutSpecimen(**kwarg)
#         elif iface.isOrExtends(specimen.TIGut):
#             newSpecimen = specimen.TIGutSpecimen(**kwarg)
#         else:
#             raise Exception('Cannot find an object for %s' % iface)
# 
#         foundSpecimen = False
# 
#         for spec in self.requestedSpecimen():
#             if newSpecimen.specimen_type == spec.specimen_type \
#                     and spec.protocol_zid == protocol_zid:
#                 foundSpecimen = True
# 
#         if not foundSpecimen:
#             sm = getSiteManager(self)
#             ds = sm.queryUtility(IDatastore, 'fia')
#             specimentmanager = ds.getSpecimenManager()
#             specimentmanager.put(IDSSpecimen(newSpecimen))




class ViewableSpecimen(grok.Adapter):
    grok.context(ISpecimen)
    grok.provides(IViewableSpecimen)
        
    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)
        
    @property
    def patient_initials(self):
        return utils.get_patient_initials(self.context.subject_zid)

    @property
    def patient_legacy_number(self):
        return utils.get_patient_legacy_number(self.context.subject_zid)
        
    @property
    def study_title(self):
        return utils.get_study_title(self.context.protocol_zid)
    
    @property
    def protocol_title(self):
        return utils.get_protocol_title(self.context.protocol_zid)
    
    @property
    def pretty_specimen_type(self):
        return self.context.specimen_type
    
    @property
    def pretty_tube_type(self):
        return self.context.tube_type
 

class ViewableAliquot(grok.Adapter):
    grok.context(IAliquot)
    grok.provides(IViewableAliquot)
        
    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)
        
    @property
    def patient_initials(self):
        return utils.get_patient_initials(self.context.subject_zid)

    @property
    def patient_legacy_number(self):
        return utils.get_patient_legacy_number(self.context.subject_zid)
        
    @property
    def study_title(self):
        return utils.get_study_title(self.context.protocol_zid)
    
    @property
    def protocol_title(self):
        return utils.get_protocol_title(self.context.protocol_zid)
    
    @property
    def pretty_aliquot_type(self):
        return self.context.aliquot_type
        
        
        
class LabeledSpecimen(grok.Adapter):
    grok.context(ISpecimen)
    grok.provides(ISpecimenLabel)

    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)

    @property
    def study_title(self):
        return utils.get_study_title(self.context.protocol_zid)
    
    @property
    def protocol_title(self):
        return utils.get_protocol_title(self.context.protocol_zid)
        
    @property
    def pretty_specimen_type(self):
        return self.context.specimen_type

    @property
    def date_collected(self):
        return self.context.date_collected
        