from five import grok
import zope.component
from zope.app.intid.interfaces import IIntIds
import datetime, sys
from cStringIO import StringIO
from Products.ZCatalog.interfaces import ICatalogBrain


from avrc.data.store.interfaces import IDatastore
from hive.lab.interfaces.specimen import ISpecimen
from hive.lab.interfaces.aliquot import IAliquot

from avrc.aeh.content.visit import IVisit
from avrc.aeh.content.patient import IPatient

from hive.lab import utilities as utils
from hive.lab.interfaces.aliquot import IViewableAliquot
from hive.lab.interfaces.aliquot import IAliquotGenerator

from hive.lab.interfaces.specimen import IBlueprintForSpecimen
from hive.lab.interfaces.labels import ILabelSheet
from hive.lab.interfaces.labels import ILabel
from hive.lab.interfaces.aliquot import IAliquotFilterForm
from hive.lab.interfaces.lab import IResearchLab
from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.interfaces.aliquot import IAliquotSupport
from hive.lab.interfaces.managers import IAliquotManager
from hive.lab.interfaces.managers import ISpecimenManager
from hive.lab.interfaces.specimen import IViewableSpecimen
from hive.lab.interfaces.specimen import IFilter
from hive.lab.interfaces.specimen import ISpecimenFilterForm
from hive.lab.interfaces.lab import IFilter
from hive.lab.interfaces.lab import IFilterForm

from hive.lab.interfaces.specimen import ISpecimenLabel
from hive.lab.content.factories import LabelGenerator
from hive.lab import MessageFactory as _

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from sqlalchemy import or_

from hive.lab.content.objects import Specimen
from hive.lab.content.objects import Aliquot

from hive.lab import model
from avrc.data.store._manager import AbstractDatastoreConventionalManager
from avrc.data.store import model as dsmodel


class ViewableSpecimen(grok.Adapter):
    grok.context(ISpecimen)
    grok.provides(IViewableSpecimen)

    @property
    def state(self):
        return self.context.state
        
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
    def dsid(self):
        return self.context.dsid

    @property
    def state(self):
        return self.context.state

    @property
    def patient_title(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_patient_title(specimenobj.subject_zid)

    @property
    def patient_legacy_number(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_patient_legacy_number(specimenobj.subject_zid)

    @property
    def study_title(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_study_title(specimenobj.protocol_zid)

    @property
    def protocol_title(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_protocol_title(specimenobj.protocol_zid)

    @property
    def study_week(self):
        return "%s - %s" % (self.study_title, self.protocol_title)

    @property
    def pretty_aliquot_type(self):
        return self.context.type

    @property
    def special_instructions(self):
        return self.context.special_instructions

##  For the checkout display
    @property
    def vol_count(self):
        if self.context.volume is not None:
            return self.context.volume
        else:
            return self.context_cell_amount

    @property
    def store_date(self):
        return self.context.store_date

    @property
    def frb(self):
        f = '?'
        r = '?'
        b = '?'
        if self.context.freezer is not None:
            f = self.context.freezer
        if self.context.rack is not None:
            r = self.context.rack
        if self.context.box is not None:
            b = self.context.box
        return "%s/%s/%s" % (f, r, b)
#     @property
#     def freezer(self):
#         return self.context.freezer
# 
#     @property
#     def rack(self):
#         return self.context.rack
# 
#     @property
#     def box(self):
#         return self.context.box


class AliquotGenerator(grok.Adapter):
    grok.context(IAliquot)
    grok.provides(IAliquotGenerator)

    @property
    def count(self):
        return None

class BlueprintForSpecimen(grok.Adapter):
    grok.context(ISpecimen)
    grok.provides(IBlueprintForSpecimen)
    """
    """
    def getBlueprint(self, context):
        intids = zope.component.getUtility(IIntIds)
        if hasattr(self.context, 'blueprint_zid') and self.context.blueprint_zid is not None:
            return intids.getObject(int(self.context.blueprint_zid))
        else:
            raise Exception('Not using newest version. please fix manually')
            return None


class LabeledSpecimen(grok.Adapter):
    grok.provides(ILabel)
    grok.context(ISpecimen)

    @property
    def dsid(self):
        return self.context.dsid

    @property
    def patient_title(self):
        return utils.get_patient_title(self.context.subject_zid)

    @property
    def study_title(self):
        return utils.get_study_title(self.context.protocol_zid)

    @property
    def protocol_title(self):
        return str(utils.get_protocol_title(self.context.protocol_zid))

    @property
    def pretty_type(self):
        return self.context.specimen_type

    @property
    def date(self):
        if self.context.date_collected is not None:
            date = self.context.date_collected.strftime("%m/%d/%Y")
        else:
            date = datetime.date.today().strftime("%m/%d/%Y")
        return date

    @property
    def barcodeline(self):
        return - 1

    @property
    def label_lines(self):
        """
        Generate the lines for a Specimen Label
        """
        line1 = unicode(' '.join([self.patient_title, self.date]))
        line2 = unicode(' '.join([self.study_title, self.protocol_title]))
        line3 = unicode(self.pretty_type)
        return [line1, line2, line3]


class LabeledAliquot(grok.Adapter):
    grok.provides(ILabel)
    grok.context(IAliquot)

    @property
    def dsid(self):
        return self.context.dsid

    @property
    def patient_title(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_patient_title(specimenobj.subject_zid)

    @property
    def study_title(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_study_title(specimenobj.protocol_zid)

    @property
    def protocol_title(self):
        specimenobj = utils.get_specimen(self.context.specimen_dsid)
        return utils.get_protocol_title(specimenobj.protocol_zid)
    @property
    def pretty_type(self):
        parts = []
        if self.context.cell_amount:
            parts.append("%sx10^6" % self.context.cell_amount)
        elif self.context.volume:
            parts.append("%smL" % self.context.volume)
        if self.context.special_instruction and self.context.special_instruction != u'na':
            parts.append(self.context.special_instruction)
        return "%s %s" % (self.context.type, " ".join(parts))

    @property
    def barcodeline(self):
        return 0

    @property
    def date(self):
        if self.context.store_date is not None:
            date = self.context.store_date.strftime("%m/%d/%Y")
        else:
            date = datetime.date.today().strftime("%m/%d/%Y")
        return date

    @property
    def label_lines(self):
        """
        Generate the lines for an Aliquot Label
        """
        ## Barcode Line
        line1 = unicode(self.dsid)
        line2 = unicode('%s OUR# %s ' % (self.dsid, self.patient_title))
        line3 = unicode(self.date)
        line4 = unicode(self.pretty_type)
        return [line1, line2, line3, line4]


class LabelFromBrain(grok.Adapter):
    grok.provides(ILabel)
    grok.context(ICatalogBrain)

    @property
    def dsid(self):
        return self.context['dsid']

    @property
    def patient_title(self):
        return self.context['patient_title']

    @property
    def study_title(self):
        return self.context['study_title']

    @property
    def protocol_title(self):
        return self.context['protocol_title']

    @property
    def pretty_type(self):
        return self.context['pretty_type']

    @property
    def barcodeline(self):
        return self.context['barcodeline']

    @property
    def date(self):
        return self.context['date']

    @property
    def label_lines(self):
        return self.context['label_lines']


class LabelPrinter(grok.Adapter):
    """
    Print a set of labels
    """
    grok.implements(ILabelPrinter)
    grok.context(ILabelSheet)

    def getLabelQue(self):
        lab = self.context
        return lab['labels']

    def getLabelBrains(self):
        quelist = []
        que = self.getLabelQue()
        for labelable in que():
            quelist.append(labelable)
        return quelist

    def queLabel(self, labelable, uid=None):
        """
        Add a label to the cue
        """
        label = ILabel(labelable)
        que = self.getLabelQue()
        if uid is None:
            uid = label.dsid
        que.catalog_object(label, uid=str(uid))

    def purgeLabel(self, uid):
        """
        Remove a label from the que
        """
        que = self.getLabelQue()
        que.uncatalog_object(str(uid))

    def printLabelSheet(self, label_list, startcol=None, startrow=None):
        """
        Create the label page, and output
        """
        stream = StringIO()
        labelWriter = LabelGenerator(self.context, stream)
        for labelable in label_list:
            label = ILabel(labelable)
            labelWriter.createLabel(label.label_lines, label.barcodeline, startcol, startrow)
        labelWriter.writeLabels()
        content = stream.getvalue()
        stream.close()
        return content


# --------------------------------------------------------------------------
# Adapters to provide an AliquotFilter to various object types
# --------------------------------------------------------------------------

class LabFilter(grok.Adapter):
    """
    Filter Aliquot by Patient
    """
    grok.implements(IFilter)
    grok.context(IResearchLab)

    def getOmittedFields(self):
        omitted=[]
        return omitted
        
    def getFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item based on an existing set of keys
        """
        intids = zope.component.getUtility(IIntIds)
        zid = intids.getId(self.context)
        retkw = {}
        for key in IFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all' or key == 'patient':
                    continue
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        return retkw


class PatientFilter(grok.Adapter):
    """
    Filter Aliquot by Patient
    """
    grok.implements(IFilter)
    grok.context(IPatient)

    def getOmittedFields(self):
        omitted=['patient']
        return omitted
    
    def getFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item based on an existing set of keys
        """
        intids = zope.component.getUtility(IIntIds)
        subject = self.context
        subject_zid = intids.getId(subject)
        retkw = {}
        for key in IFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all' or key == 'patient':
                    continue
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        retkw['subject_zid'] = subject_zid
        return retkw


class VisitFilter(grok.Adapter):
    """
    Filter Aliquot by Patient
    """
    grok.implements(IFilter)
    grok.context(IVisit)


    def getOmittedFields(self):
        omitted=['patient', 'before_date','after_date']
        return omitted
        
    def getFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item
        """
        retkw = {}
        intids = zope.component.getUtility(IIntIds)
        subject = self.context.aq_parent
        subject_zid = intids.getId(subject)
        protocols = self.context.cycles
        date_collected = self.context.visit_date
        cyclelist = []
        for protocol in protocols:
            cyclelist.append(protocol.to_id)
        for key in IFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all' or key == 'patient':
                    continue
                else:
                    retkw[key] = basekw[key]
        retkw['subject_zid'] = subject_zid
        retkw['protocol_zid'] = cyclelist
        return retkw

# ----------------------------------------------------------------------
#
# Data Store Managers
#
# ----------------------------------------------------------------------
class DatastoreSpecimenManager(AbstractDatastoreConventionalManager, grok.Adapter):
    grok.context(IDatastore)
    grok.provides(ISpecimenManager)

    _model = model.Specimen
    _type = Specimen


    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """

    def get(self, key):
        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model

        specimen_rslt = Session.query(SpecimenModel)\
                        .filter_by(id=int(key))\
                        .first()

        return specimen_rslt and Specimen.from_rslt(specimen_rslt) or None

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

    def filter_specimen(self, **kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """
        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model
        SubjectModel = dsmodel.Subject
        ProtocolModel = dsmodel.Protocol
        
        query = Session.query(SpecimenModel)

        if 'subject_zid' in kw and 'our_id' in kw:
            del kw['our_id']

        for key, item in kw.items():
            if not isinstance(item, list):
                item = [item]

            filters = []

            for value in item:
                if value is not None:
                    if key == 'state':
                        filter = SpecimenModel.state.has(value=unicode(value))
                    elif key == 'specimen_type':
                        filter = SpecimenModel.type.has(value=unicode(value))
                    elif key == 'before_date':
                        filter = SpecimenModel.collect_date <= value
                    elif key == 'after_date':
                        filter = SpecimenModel.collect_date >= value
                    elif key == 'protocol_zid':
                        filter = SpecimenModel.protocol.has(zid=value)
                    elif key == 'our_id':
                        filter = SpecimenModel.subject.has(uid=value)
                    elif key == 'subject_zid':
                        filter = SpecimenModel.subject.has(zid=value)
                    else:
                        print '%s is not a valid filter' % key
                        filter = None

                    if filter is not None:
                        filters.append(filter)

            filter = or_(*filters)
            query = query.filter(filter)

        query = query.order_by(SpecimenModel.id.desc()).limit(200)
        result = [Specimen.from_rslt(r) for r in query.all()]
        return result


    def list_by_state(self, state, before_date=None, after_date=None):
        """ 
        deprecated function. use filter_specimen instead
        """
        kw = {
            'state': state,
            'before_date':before_date,
            'after_date':after_date
        }
        return self.filter_specimen(**kw)

    def list_specimen_by_group(self,
                               protocol_zid=None,
                               subject_zid=None,
                               state=None,
                               specimen_type=None):
        """ 
        deprecated function. use filter_specimen instead
        """
        kw = {
            'protocol_zid': protocol_zid,
            'subject_zid':subject_zid,
            'state':state,
            'specimen_type':specimen_type
        }
        return self.filter_specimen(**kw)


    def put(self, source):

        Session = self._datastore.getScopedSession()
        SpecimenModel = self._model

        # Find the 'vocabulary' objects for the database relation
        keywords = {"state": u"specimen_state",
                    "tube_type": u"specimen_tube_type",
                    "destination": u"specimen_destination",
                    "specimen_type": u"specimen_type"
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
            specimen_rslt = Session.query(SpecimenModel)\
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
            specimen_rslt = SpecimenModel(
                subject=subject_rslt,
                protocol=protocol_rslt,
                type=rslt["specimen_type"],
                )

            Session.add(specimen_rslt)

        specimen_rslt.blueprint_zid = source.blueprint_zid
        specimen_rslt.destination = rslt["specimen_destination"]
        specimen_rslt.state = rslt["specimen_state"]
        specimen_rslt.collect_date = source.date_collected
        specimen_rslt.collect_time = source.time_collected
        specimen_rslt.tubes = source.tubes
        specimen_rslt.tube_type = rslt["specimen_tube_type"]
        specimen_rslt.notes = source.notes

        Session.flush()

        if not source.dsid:
            source.dsid = specimen_rslt.id

        return source

    def aliquot(self, key):
        return IAliquotManager(self._datastore, self.get(key))


class DatastoreAliquotManager(AbstractDatastoreConventionalManager, grok.Adapter):
    grok.context(IDatastore)
    grok.provides(IAliquotManager)

    _model = model.Aliquot
    _type = Aliquot


    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """

    def get(self, key):
        Session = self._datastore.getScopedSession()
        AliquotModel = self._model

        aliquot_rslt = Session.query(AliquotModel)\
                        .filter_by(id=int(key))\
                        .first()

        return aliquot_rslt and Aliquot.from_rslt(aliquot_rslt) or None


    def filter_aliquot(self, **kw):
        """
        Generic aliquot filter. Takes kw arguments, generally matching
        the IAliquot interface
        """
        Session = self._datastore.getScopedSession()
        AliquotModel = self._model
        SpecimenModel = model.Specimen

        query = Session.query(AliquotModel)

        if 'subject_zid' in kw and 'our_id' in kw:
            del kw['our_id']

        for key, item in kw.items():
            if not isinstance(item, list):
                item = [item]

            filters = []

            for value in item:
                if value is not None:
                    if key == 'state':
                        filter = AliquotModel.state.has(value=unicode(value))
                    elif key == 'type':
                        filter = AliquotModel.type.has(value=unicode(value))
                    elif key == 'before_date':
                        filter = AliquotModel.store_date <= value
                    elif key == 'after_date':
                        filter = AliquotModel.store_date >= value
                    elif key == 'protocol_zid':
                        filter = AliquotModel.specimen.has(SpecimenModel.protocol.has(zid=value))
                    elif key == 'our_id':
                        filter = AliquotModel.specimen.has(SpecimenModel.subject.has(uid=value))
                    elif key == 'subject_zid':
                        filter = AliquotModel.specimen.has(SpecimenModel.subject.has(zid=value))
                    else:
                        print '%s is not a valid filter' % key
                        filter = None

                    if filter is not None:
                        filters.append(filter)

            filter = or_(*filters)
            query = query.filter(filter)

        query = query.order_by(AliquotModel.id.desc()).limit(200)
        result = [Aliquot.from_rslt(r) for r in query.all()]
        return result


    def list_by_state(self, state, our_id=None, before_date=None, after_date=None):
        """ 
        deprecated function. use filter_specimen instead
        """
        kw = {
            'our_id': our_id,
            'state': state,
            'before_date':before_date,
            'after_date':after_date
        }
        return self.filter_aliquot(**kw)


    def list_aliquot_by_group(self,
                              protocol_zid=None,
                              subject_zid=None,
                              state=None):
        """ """

        kw = {
            'state': state,
            'protocol_zid':before_date,
            'subject_zid':after_date
        }
        return self.filter_aliquot(**kw)


    def put(self, source):

        Session = self._datastore.getScopedSession()
        AliquotModel = self._model

        # Find the 'vocabulary' objects for the database relation
        keywords = {"state": u"aliquot_state",
                    "type": u"aliquot_type",
                    "storage_site": u"aliquot_storage_site",
                    "analysis_status": u"aliquot_analysis_status",
                    "special_instruction": u"aliquot_special_instruction",
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
            aliquot_rslt = Session.query(AliquotModel)\
                            .filter_by(id=source.dsid)\
                            .first()
        else:
            # which enrollment we get the subject from.
            specimen_rslt = Session.query(model.Specimen)\
                            .filter_by(id=source.specimen_dsid)\
                            .first()

            # specimen is not already in the data base, we need to create one
            aliquot_rslt = AliquotModel(
                specimen=specimen_rslt,
                type=rslt["aliquot_type"],
                )

            Session.add(aliquot_rslt)

        aliquot_rslt.analysis_status = rslt["aliquot_state"]
        aliquot_rslt.sent_date = source.sent_date
        aliquot_rslt.sent_name = source.sent_name
        aliquot_rslt.special_instruction = rslt["aliquot_special_instruction"]
        aliquot_rslt.storage_site = rslt["aliquot_storage_site"]
        aliquot_rslt.state = rslt["aliquot_state"]
        aliquot_rslt.volume = source.volume
        aliquot_rslt.cell_amount = source.cell_amount
        aliquot_rslt.store_date = source.store_date
        aliquot_rslt.freezer = source.freezer
        aliquot_rslt.rack = source.rack
        aliquot_rslt.box = source.box
        aliquot_rslt.thawed_num = source.thawed_num
        aliquot_rslt.notes = source.notes

        Session.flush()

        if not source.dsid:
            source.dsid = aliquot_rslt.id

        return source
