# from avrc.aeh import model as dsmodel
# from avrc.data.store.interfaces import IDataStore
# from hive.lab import model
# from hive.lab.interfaces.managers import IAliquotManager, \
#                                          ISpecimenManager
# from sqlalchemy import or_
# from zope.component import adapts
# from zope.interface import implements
# from zope.schema.vocabulary import SimpleTerm, \
#                                    SimpleVocabulary


# # ----------------------------------------------------------------------
# # Data Store Managers
# # ----------------------------------------------------------------------

# class BaseConventionalManager(object):
#     """
#     """
#     _Model = None
#     _Vocab = None

#     def __init__(self, datastore):
#         self.datastore = datastore
        
#     def get(self, key):
#         """ See `IBaseConventionalManager.get`
#         """
#         session = self.datastore.session
#         result = session.query(self._Model)\
#             .filter_by(id=int(key), is_active=True)\
#             .first()
#         return result and result.objectify() or None

#     def keys(self, on=None, ever=False):
#         raise NotImplementedError

#     def lifecycles(self, key):
#         raise NotImplementedError

#     def has(self, key, on=None, ever=False):
#         """ see `IBaseConventionalManager.has`
#         """
#         session = self.datastore.session
#         result = session.query(self._Model)\
#             .filter_by(id=int(key), is_active=True)\
#             .first()
#         return result and True or False

#     def purge(self, key, on=None, ever=False):
#         raise NotImplementedError

#     def retire(self, key):
#         """ See `IBaseConventionalManager.retire`
#         """
#         session = self.datastore.session
#         if key is not None:
#             result = session.query(self._Model) \
#                 .filter_by(id=key) \
#                 .first()
#         if result:
#             result.is_active = False
#             session.flush()
#         else:
#             raise Exception('Invalid Key')
#         return None

#     def restore(self, key):
#         """ See `IBaseConventionalManager.restore`
#         """
#         session = self.datastore.session
#         if key is not None:
#             result = session.query(self._Model) \
#                 .filter_by(id=key) \
#                 .first()
#         if result:
#             result.is_active = True
#             session.flush()
#             return result.objectify()
#         else:
#             raise Exception('Invalid Key')
#         return None

#     def get_vocabulary(self, name):
#         """ Utility method for retrieving supported vocabulary terms for
#             specimen and aliquot attributes.

#             Arguments:
#                 name: (unicode) the name of the vocabulary to fetch
#             Returns:
#                 SimpleVocabulary object
#         """
#         session = self.datastore.session

#         term_list = []
#         term_q = session.query(self._Vocab)\
#                   .filter_by(vocabulary_name=name)

#         for term_rslt in term_q.all():
#             term_list.append(SimpleTerm(
#                 value=term_rslt.value,
#                 token=term_rslt.token,
#                 title=term_rslt.title
#                 ))
#         return SimpleVocabulary(term_list)

#     def vocab_map(self, source, **kw):
#         """
#         see IBaseConventionalManager.vocab_map
#         """
#         session = self.datastore.session
#         map = {}
#         for attr_name, vocab_name in kw.items():
#             value = getattr(source, attr_name, None)

#             if value:
#                 map[vocab_name] = session.query(self._Vocab)\
#                                 .filter_by(vocabulary_name=vocab_name,
#                                            value=value
#                                            )\
#                                 .first()
#             else:
#                 map[vocab_name] = None
#         return map

#     def makefilter(self, **kw):
#         """
#         """
#         raise NotImplementedError

#     def count_records(self, **kw):
#         """ see ISpecimenManager.count_records
#         """
#         query = self.makefilter(**kw)
#         result = query.count()
#         return result
        
#     def filter_records(self, **kw):
#         """
#         Generic specimen filter. Takes kw arguments, generally matching
#         the ISpecimen interface
#         """
#         query = self.makefilter(**kw)
#         result = [r.objectify() for r in query.all()]
#         return result
    
# ## -----------------------------------------------------------
# # TODO: damote - Move this to a  setup script
# ## -----------------------------------------------------------
# #     def setupVocabulary(self, vocabularies):
# #         """
# #         """
# #         session = self.datastore.session
# #         for vocabulary_name, vocabulary_obj in vocabularies.items():
# #             for term_obj in vocabulary_obj:
# #                 term = self._Vocab(
# #                         vocabulary_name=unicode(vocabulary_name),
# #                         title=term_obj.title and unicode(term_obj.title) or None,
# #                         token=unicode(term_obj.token),
# #                         value=unicode(term_obj.value)
# #                         )  
# #                 session.add(term)
# #         session.flush()



# class SpecimenManager(BaseConventionalManager):
#     adapts(IDataStore)
#     implements(ISpecimenManager)

#     _Model = model.Specimen
#     _Vocab = model.SpecimenAliquotTerm
    
#     def put(self, source, by=None):
#         """ See `ISpecimenManager.put`
#         """
#         session = self.datastore.session

#         ### Build Specimen Vocabulary
#         kw = {"state": u"specimen_state",
#               "tube_type": u"specimen_tube_type",
#               "destination": u"specimen_destination",
#               "type": u"specimen_type"
#               }
              
#         map = self.vocab_map(source, **kw)
        
#         if source.dsid is not None:
#             entry = session.query(model.Specimen) \
#                 .filter_by(id=source.dsid) \
#                 .first()

#         else:
#             # which enrollment we get the subject from.
#             subject = session.query(dsmodel.Subject)\
#                         .filter_by(zid=source.subject_zid)\
#                         .first()

#             protocol = session.query(dsmodel.Protocol)\
#                         .filter_by(zid=source.protocol_zid)\
#                         .first()
                            
#             # specimen is not already in the data base, we need to create one
#             entry = model.Specimen()
#             entry.subject = subject
#             entry.protocol = protocol
#             entry.type = type = map["specimen_type"]
#             session.add(entry)

#         entry.blueprint_zid = source.blueprint_zid
#         entry.destination = map["specimen_destination"]
#         entry.state = map["specimen_state"]
#         entry.collect_date = source.date_collected
#         entry.collect_time = source.time_collected
#         entry.tubes = source.tubes
#         entry.tube_type = map["specimen_tube_type"]
#         entry.notes = source.notes

#         if not source.dsid:
#             source.dsid = entry.id
#         return source

#     def makefilter(self, **kw):
#         """ see ISpecimenManager.makefilter
#         """
#         session = self.datastore.session
#         query = session.query(model.Specimen)

#         if 'subject_zid' in kw and 'our_id' in kw:
#             del kw['our_id']

#         for key, item in kw.items():
#             if not isinstance(item, list):
#                 item = [item]

#             filters = []
#             for value in item:
#                 if value is not None:
#                     if key == 'state':
#                         filter = model.Specimen.state.has(value=unicode(value))
#                     elif key == 'type':
#                         filter = model.Specimen.type.has(value=unicode(value))
#                     elif key == 'before_date':
#                         filter = model.Specimen.collect_date <= value
#                     elif key == 'after_date':
#                         filter = model.Specimen.collect_date >= value
#                     elif key == 'protocol_zid':
#                         filter = model.Specimen.protocol.has(zid=value)
#                     elif key == 'our_id':
#                         filter = model.Specimen.subject.has(uid=value)
#                     elif key == 'subject_zid':
#                         filter = model.Specimen.subject.has(zid=value)
#                     elif key == 'modify_name':
#                         if value is not None:
#                             filter = model.Specimen.modify_name == unicode(value)
#                         else:
#                             filter = None
#                     else:
#                         print '%s is not a valid filter' % key
#                         filter = None

#                     if filter is not None:
#                         filters.append(filter)

#             if len(filters):
#                 filter = or_(*filters)
#                 query = query.filter(filter)

#         query = query.order_by(model.Specimen.id.desc())
#         return query

# #     def aliquot(self, key):
# #         return IAliquotManager(self.datastore, self.get(key))


# class AliquotManager(BaseConventionalManager):
#     adapts(IDataStore)
#     implements(IAliquotManager)

#     _Model = model.Aliquot
#     _Vocab = model.SpecimenAliquotTerm

#     def put(self, source, by=None):
#         session = self.datastore.session
#         kw = dict(
#                 state=u"aliquot_state",
#                 type=u"aliquot_type",
#                 storage_site=u"aliquot_storage_site",
#                 analysis_status=u"aliquot_analysis_status",
#                 special_instruction=u"aliquot_special_instruction",
#             )
            
#         previous_state_id = None
#         map = self.vocab_map(source, **kw)
#         if source.dsid is not None:
#             entry = session.query(model.Aliquot).get(source.dsid)
#             previous_state = entry.state
#         else:
#             # which enrollment we get the subject from.
#             specimen = session.query(model.Specimen).get(source.specimen_dsid)
#             # specimen is not already in the data base, we need to create one
#             entry = model.Aliquot(specimen=specimen, type=map["aliquot_type"], create_name=by)
#             previous_state = map["aliquot_state"]
#             session.add(entry)

#         entry.analysis_status = map["aliquot_state"]
#         entry.sent_date = source.sent_date
#         entry.sent_name = source.sent_name
#         entry.special_instruction = map["aliquot_special_instruction"]
#         entry.storage_site = map["aliquot_storage_site"]
#         entry.state = map["aliquot_state"]
#         entry.volume = source.volume
#         entry.cell_amount = source.cell_amount
#         entry.store_date = source.store_date
#         entry.freezer = source.freezer
#         entry.rack = source.rack
#         entry.box = source.box
#         entry.inventory_date = source.inventory_date
#         entry.thawed_num = source.thawed_num
#         entry.notes = source.notes
#         entry.sent_notes = source.sent_notes
#         entry.modify_name = by

#         if previous_state.id != entry.state.id:
#             history = model.AliquotHistory(
#                 aliquot=entry,
#                 from_state=previous_state,
#                 to_state=entry.state,
#                 action_date=model.NOW,
#                 create_name=by,
#                 )
#             session.add(history)

#         session.flush()

#         if not source.dsid:
#             source.dsid = entry.id
#         return source

#     def makefilter(self, **kw):
#         """
#         Generic aliquot filter. Takes kw arguments, generally matching
#         the IAliquot interface
#         """
#         session = self.datastore.session
#         query = session.query(model.Aliquot)

#         if 'subject_zid' in kw and 'our_id' in kw:
#             del kw['our_id']
#         for key, item in kw.items():
#             if not isinstance(item, list):
#                 item = [item]

#             filters = []
#             for value in item:
#                 if value is not None:

#                     if key == 'state':
#                         filter = model.Aliquot.state.has(value=unicode(value))
#                     elif key == 'type':
#                         filter = model.Aliquot.type.has(value=unicode(value))
#                     elif key == 'freezer':
#                             filter = model.Aliquot.freezer == unicode(value)
#                     elif key == 'rack':
#                             filter = model.Aliquot.rack == unicode(value)
#                     elif key == 'box':
#                             filter = model.Aliquot.box == unicode(value)
#                     elif key == 'inventory_date':
#                             filter = ((model.Aliquot.inventory_date <= value) | (model.Aliquot.inventory_date == None))
#                     elif key == 'before_date':
#                         filter = model.Aliquot.store_date <= value 
#                     elif key == 'after_date':
#                         filter = model.Aliquot.store_date >= value
#                     elif key == 'protocol_zid':
#                         filter = model.Aliquot.specimen.has(model.Specimen.protocol.has(zid=value))
#                     elif key == 'our_id':
#                         filter = model.Aliquot.specimen.has(model.Specimen.subject.has(uid=value))
#                     elif key == 'subject_zid':
#                         filter = model.Aliquot.specimen.has(model.Specimen.subject.has(zid=value))
#                     elif key == 'modify_name':
#                         if value is not None:
#                             filter = model.Aliquot.modify_name == unicode(value)
#                         else:
#                             filter = None
#                     else:
#                         print '%s is not a valid filter' % key
#                         filter = None

#                     if filter is not None:
#                         filters.append(filter)

#             if len(filters):
#                 filter = or_(*filters)
#                 query = query.filter(filter)

#         query = query.order_by(model.Aliquot.id.desc())
#         return query

