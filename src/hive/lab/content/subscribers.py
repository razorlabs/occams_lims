
from hive.lab.interfaces.labels import ILabelSheet
from hive.lab.interfaces.lab import IContainsSpecimen
from hive.lab.interfaces.specimen import IRequestSpecimen

from five import grok
from zope.lifecycleevent import IObjectAddedEvent
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
from hive.lab import MessageFactory as _

    
@grok.subscribe(ILabelSheet, IObjectAddedEvent)
def handleLabelSheetAdded(sheet, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site.
    """
    manage_addZCatalog(sheet, 'labels', u'Labels', REQUEST=None)
    zcat = sheet._getOb('labels')
    label_catalog = zcat._catalog
    for field in ['patient_title', 'study_title', 'protocol_title', 'pretty_specimen_type']:
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)
    dateindex = DateIndex('date_collected')
    label_catalog.addIndex('date_collected', dateindex)  
    label_catalog.addColumn('date_collected')


@grok.subscribe(IRequestSpecimen, IObjectAddedEvent)
def handleSpecimenRequestorAdd(item, event):
    """
    Create New Specimen, based on the blueprint, with the following fields:
    subject_zid

    protocol_zid

    state

    date_collected

    time_collected

    specimen_type

    destination

    tubes

    tube_type

    notes
    
    """
    
    intids = component.getUtility(IIntIds)
    patient = self.aq_parent
    patient_zid = intids.getId(patient)
    specimen_state = u'pending-draw'
    import pdb;pdb.set_trace()
    for cycle in item.cycles:
        for bp in cycle.related_specimen:
            blueprint = bp.to_object
            
            
# #             visit.addRequestedSpecimen(iface=iface, protocol_zid=int(cycleid))


# #     obj = visit_manager.put(IDSVisit(visit))

# #     def addRequestedSpecimen(self, iface=None, protocol_zid=None):
# #         """ """
# #         intids = component.getUtility(IIntIds)
# #         patient = self.aq_parent
# #         patient_zid = intids.getId(patient)
# # 
# #         kwarg = {
# #             'date_collected': self.visit_date,
# #             'subject_zid': int(patient_zid),
# #             'protocol_zid': protocol_zid
# #             }
# # 
# #         newSpecimen = None
# # 
# #         if iface.isOrExtends(specimen.ACD):
# #             newSpecimen = specimen.ACDSpecimen(**kwarg)
# #         elif iface.isOrExtends(specimen.AnalSwab):
# #             newSpecimen = specimen.AnalSwabSpecimen(**kwarg)
# #         elif iface.isOrExtends(specimen.CSF):
# #             newSpecimen = specimen.CSFSpecimen(**kwarg)
# #         elif iface.isOrExtends(specimen.GenitalSecretions):
# #             newSpecimen = specimen.GSSpecimen(**kwarg)
# #         elif iface.isOrExtends(specimen.Serum):
# #             newSpecimen = specimen.SerumSpecimen(**kwarg)
# #         elif iface.isOrExtends(specimen.RSGut):
# #             newSpecimen = specimen.RSGutSpecimen(**kwarg)
# #         elif iface.isOrExtends(specimen.TIGut):
# #             newSpecimen = specimen.TIGutSpecimen(**kwarg)
# #         else:
# #             raise Exception('Cannot find an object for %s' % iface)
# # 
# #         foundSpecimen = False
# # 
# #         for spec in self.requestedSpecimen():
# #             if newSpecimen.specimen_type == spec.specimen_type \
# #                     and spec.protocol_zid == protocol_zid:
# #                 foundSpecimen = True
# # 
# #         if not foundSpecimen:
# #             sm = getSiteManager(self)
# #             ds = sm.queryUtility(IDatastore, 'fia')
# #             specimentmanager = ds.getSpecimenManager()
# #             specimentmanager.put(IDSSpecimen(newSpecimen))


# @grok.subscribe(IContainsSpecimen, IObjectAddedEvent)
# def handleSpecimenContainerAdded(lab, event):
#     """ Research Lab added event handler.
#         This method will be triggered when an Research Lab is added to the
#         current Site.
#     """
#     manage_addZCatalog(lab, 'blueprints', u'Labels', REQUEST=None)
#     blueprint_cat = lab._getOb('blueprints')
#     blueprint_catalog = blueprint_cat._catalog
#     for field in ['id', 'title', 'portal_type', 'specimen_type_title', 'specimen_type','default_tubes','tube_type_title','tube_type', 'pretty_aliquot_type']:
#         index = FieldIndex(field)
#         blueprint_catalog.addIndex(field, index)
#         blueprint_catalog.addColumn(field)
# #     dateindex = DateIndex('date_collected')
# #     label_catalog.addIndex('date_collected', dateindex)  
# #     label_catalog.addColumn('date_collected')
