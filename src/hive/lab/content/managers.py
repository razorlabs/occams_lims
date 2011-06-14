from avrc.data.store import model as dsmodel
from avrc.data.store._manager import AbstractDatastoreConventionalManager
from avrc.data.store.interfaces import IDatastore
from five import grok
from hive.lab import model
from hive.lab.content.objects import Aliquot, \
                                     Specimen

from hive.lab.interfaces.managers import IAliquotManager, \
                                         ISpecimenManager

from sqlalchemy import or_
from zope.schema.vocabulary import SimpleTerm, \
                                   SimpleVocabulary

# ----------------------------------------------------------------------
# Data Store Managers
# ----------------------------------------------------------------------

class DatastoreManagercore(AbstractDatastoreConventionalManager):

    _model = None
    _type = None

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """

    def get(self, key):
        Session = self._datastore.getScopedSession()
        Model = self._model
        Object = self._type

        record_rslt = Session.query(Model)\
                        .filter_by(id=int(key))\
                        .first()

        return record_rslt and Object.from_rslt(record_rslt) or None

    def get_vocabulary(self, name):
        """ Utility method for retrieving supported vocabulary terms for
            specimen and aliquot attributes.

            Arguments:
                name: (unicode) the name of the vocabulary to fetch
            Returns:
                SimpleVocabulary object
        """
        Session = self._datastore.getScopedSession()

        term_list = []
        term_q = Session.query(model.SpecimenAliquotTerm)\
                  .filter_by(vocabulary_name=name)

        for term_rslt in term_q.all():
            term_list.append(SimpleTerm(
                value=term_rslt.value,
                token=term_rslt.token,
                title=term_rslt.title
                ))

        return SimpleVocabulary(term_list)

    def setupVocabulary(self, vocabularies):
        Session = self._datastore.getScopedSession()

        for vocabulary_name, vocabulary_obj in vocabularies.items():
            for term_obj in vocabulary_obj:
                Session.add(model.SpecimenAliquotTerm(
                    vocabulary_name=unicode(vocabulary_name),
                    title=term_obj.title and unicode(term_obj.title) or None,
                    token=unicode(term_obj.token),
                    value=unicode(term_obj.value)
                    ))

        Session.flush()

    def filter_records(self, **kw):
            raise NotImplementedError

class DatastoreSpecimenManager(DatastoreManagercore, grok.Adapter):
    grok.context(IDatastore)
    grok.provides(ISpecimenManager)

    _model = model.Specimen
    _type = Specimen

    def getFilter(self, **kw):

        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """
        Session = self._datastore.getScopedSession()
        Model = self._model

        query = Session.query(Model)

        if 'subject_zid' in kw and 'our_id' in kw:
            del kw['our_id']

        for key, item in kw.items():
            if not isinstance(item, list):
                item = [item]

            filters = []

            for value in item:
                if value is not None:
                    if key == 'state':
                        filter = Model.state.has(value=unicode(value))
                    elif key == 'type':
                        filter = Model.type.has(value=unicode(value))
                    elif key == 'before_date':
                        filter = Model.collect_date <= value
                    elif key == 'after_date':
                        filter = Model.collect_date >= value
                    elif key == 'protocol_zid':
                        filter = Model.protocol.has(zid=value)
                    elif key == 'our_id':
                        filter = Model.subject.has(uid=value)
                    elif key == 'subject_zid':
                        filter = Model.subject.has(zid=value)
                    elif key == 'modify_name':
                        filter = Model.modify_name == unicode(value)
                    else:
                        print '%s is not a valid filter' % key
                        filter = None

                    if filter is not None:
                        filters.append(filter)

            if len(filters):
                filter = or_(*filters)
                query = query.filter(filter)

        query = query.order_by(Model.id.desc()).limit(200)
        return query

    def count_records(self, **kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """

        Object = self._type
        query = self.getFilter(**kw)
        result = query.count()
        return result
        
    def filter_records(self, **kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """

        Object = self._type
        query = self.getFilter(**kw)
        result = [Object.from_rslt(r) for r in query.all()]
        return result

    def put(self, source):

        Session = self._datastore.getScopedSession()
        Model = self._model

        # Find the 'vocabulary' objects for the database relation
        keywords = {"state": u"specimen_state",
                    "tube_type": u"specimen_tube_type",
                    "destination": u"specimen_destination",
                    "type": u"specimen_type"
                    }

        rslt = {}

        for attr_name, vocab_name in keywords.items():
            value = getattr(source, attr_name, None)

            if value:
                rslt[vocab_name] = Session.query(model.SpecimenAliquotTerm)\
                                .filter_by(vocabulary_name=vocab_name,
                                           value=value
                                           )\
                                .first()
            else:
                rslt[vocab_name] = None

        if source.dsid is not None:
            record_rslt = Session.query(Model)\
                            .filter_by(id=source.dsid)\
                            .first()
        else:
            # which enrollment we get the subject from.

            subject_rslt = Session.query(dsmodel.Subject)\
                            .filter_by(zid=source.subject_zid)\
                            .first()

            protocol_rslt = Session.query(dsmodel.Protocol)\
                            .filter_by(zid=source.protocol_zid)\
                            .first()

            # specimen is not already in the data base, we need to create one
            record_rslt = Model(
                subject=subject_rslt,
                protocol=protocol_rslt,
                type=rslt["specimen_type"],
                )

            Session.add(record_rslt)

        record_rslt.blueprint_zid = source.blueprint_zid
        record_rslt.destination = rslt["specimen_destination"]
        record_rslt.state = rslt["specimen_state"]
        record_rslt.collect_date = source.date_collected
        record_rslt.collect_time = source.time_collected
        record_rslt.tubes = source.tubes
        record_rslt.tube_type = rslt["specimen_tube_type"]
        record_rslt.notes = source.notes

        Session.flush()

        if not source.dsid:
            source.dsid = record_rslt.id

        return source

    def aliquot(self, key):
        return IAliquotManager(self._datastore, self.get(key))


class DatastoreAliquotManager(DatastoreManagercore, grok.Adapter):
    grok.context(IDatastore)
    grok.provides(IAliquotManager)

    _model = model.Aliquot
    _type = Aliquot


    def getFilter(self, **kw):
        """
        Generic aliquot filter. Takes kw arguments, generally matching
        the IAliquot interface
        """
        Session = self._datastore.getScopedSession()
        Model = self._model
        SpecimenModel = model.Specimen
        query = Session.query(Model)

        if 'subject_zid' in kw and 'our_id' in kw:
            del kw['our_id']

        for key, item in kw.items():
            if not isinstance(item, list):
                item = [item]

            filters = []
            for value in item:
                if value is not None:
                    if key == 'state':
                        filter = Model.state.has(value=unicode(value))
                    elif key == 'type':
                        filter = Model.type.has(value=unicode(value))
                    elif key == 'before_date':
                        filter = Model.store_date <= value
                    elif key == 'after_date':
                        filter = Model.store_date >= value
                    elif key == 'protocol_zid':
                        filter = Model.specimen.has(SpecimenModel.protocol.has(zid=value))
                    elif key == 'our_id':
                        filter = Model.specimen.has(SpecimenModel.subject.has(uid=value))
                    elif key == 'subject_zid':
                        filter = Model.specimen.has(SpecimenModel.subject.has(zid=value))
                    elif key == 'modify_name':
                        filter = Model.modify_name == unicode(value)
                    else:
                        print '%s is not a valid filter' % key
                        filter = None

                    if filter is not None:
                        filters.append(filter)

            if len(filters):
                filter = or_(*filters)
                query = query.filter(filter)

        query = query.order_by(Model.id.desc())
        return query

    def count_records(self, **kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """

        Object = self._type
        query = self.getFilter(**kw)
        result = query.count()
        return result

    def filter_records(self, **kw):
        """
        Generic aliquot filter. Takes kw arguments, generally matching
        the IAliquot interface
        """
        Object = self._type
        query = self.getFilter(**kw)
        result = [Object.from_rslt(r) for r in query.all()]
        return result

    def put(self, source, by=None):

        Session = self._datastore.getScopedSession()
        Model = self._model

        # Find the 'term' objects for the database relation
        column_vocabulary_map = dict(
            state=u"aliquot_state",
            type=u"aliquot_type",
            storage_site=u"aliquot_storage_site",
            analysis_status=u"aliquot_analysis_status",
            special_instruction=u"aliquot_special_instruction",
            )

        term = dict()

        previous_state_id = None

        for attr_name, vocab_name in column_vocabulary_map.items():
            value = getattr(source, attr_name, None)
            if value:
                term[vocab_name] = (
                    Session.query(model.SpecimenAliquotTerm)
                    .filter_by(vocabulary_name=vocab_name, value=value)
                    .first()
                    )
            else:
                term[vocab_name] = None

        if source.dsid is not None:
            entry = Session.query(Model).get(source.dsid)
            previous_state = entry.state
        else:
            # which enrollment we get the subject from.
            specimen = Session.query(model.Specimen).get(source.specimen_dsid)

            # specimen is not already in the data base, we need to create one
            entry = Model(specimen=specimen, type=term["aliquot_type"], create_name=by)
            previous_state = term["aliquot_state"]
            Session.add(entry)

        entry.analysis_status = term["aliquot_state"]
        entry.sent_date = source.sent_date
        entry.sent_name = source.sent_name
        entry.special_instruction = term["aliquot_special_instruction"]
        entry.storage_site = term["aliquot_storage_site"]
        entry.state = term["aliquot_state"]
        entry.volume = source.volume
        entry.cell_amount = source.cell_amount
        entry.store_date = source.store_date
        entry.freezer = source.freezer
        entry.rack = source.rack
        entry.box = source.box
        entry.thawed_num = source.thawed_num
        entry.notes = source.notes
        entry.sent_notes = source.sent_notes
        entry.modify_name = by

        if previous_state.id != entry.state.id:
            history = model.AliquotHistory(
                aliquot=entry,
                from_state=previous_state,
                to_state=entry.state,
                action_date=model.NOW,
                create_name=by,
                )
            Session.add(history)

        Session.flush()

        if not source.dsid:
            source.dsid = entry.id

        return source
