from Products.ZCatalog.interfaces import ICatalogBrain
from avrc.aeh.content.patient import IPatient
from avrc.aeh.content.visit import IVisit
from cStringIO import StringIO
from five import grok
from hive.lab import MessageFactory as _,\
                     utilities as utils
from hive.lab.content.factories import LabelGenerator

from hive.lab.interfaces.aliquot import IAliquot,\
                                        IAliquotGenerator,\
                                        IViewableAliquot,\
                                        IAliquotFilterForm
from hive.lab.interfaces.lab import IFilterForm,\
                                    IResearchLab
from hive.lab.interfaces.labels import ILabel,\
                                       ILabelPrinter,\
                                       ILabelSheet

from hive.lab.interfaces.specimen import IBlueprintForSpecimen,\
                                         IFilter,\
                                         ISpecimen,\
                                         IViewableSpecimen
from zope.app.intid.interfaces import IIntIds                         
import datetime
import zope.component

# ------------------------------------------------------------------------------
# View Adapters |
# --------------
# These classes make records from the data store human readable
# that support and modify specimen
# ------------------------------------------------------------------------------

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
    def study_week(self):
        return "%s - %s" % (self.study_title, self.protocol_title)

    @property
    def pretty_type(self):
        return self.context.type

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
        aeh = utils.get_patient_legacy_number(specimenobj.subject_zid)
        mbn = utils.get_patient_master_book_number(specimenobj.subject_zid)
        if aeh and mbn:
            ret = '%s / %s' %(aeh, mbn)
        elif aeh:
            ret = aeh
        else:
            ret = mbn
        return ret

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
    def pretty_type(self):
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

# ------------------------------------------------------------------------------
# Aliquoting Tools|
# --------------
# These classes assist with the aliquoting of specimen
# ------------------------------------------------------------------------------

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
        
# ------------------------------------------------------------------------------
# Filter Tools|
# --------------
# These classes provide default filters for records based on context
# ------------------------------------------------------------------------------

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
        retkw = {}
        for key in IFilterForm.names():
        
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all':
                    continue
                elif key == 'patient':
                    retkw['subject_zid'] = utils.getPatientForFilter(self.context, basekw[key])
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


# ------------------------------------------------------------------------------
# Label Tools Tools|
# --------------
# These classes provide templates for turning records into printable
# labesl
# ------------------------------------------------------------------------------


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
        return self.context.type

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

    def getLabelQueue(self):
        lab = self.context
        return lab['labels']

    def getLabelBrains(self):
#         queuelist = []
        queue = self.getLabelQueue()
#for labelable in
        return queue(sort_on='dsid', sort_order='ascending')
#            queuelist.append(labelable)
#        return queuelist

    def queueLabel(self, labelable, uid=None):
        """
        Add a label to the cue
        """
        label = ILabel(labelable)
        queue = self.getLabelQueue()
        if uid is None:
            uid = label.dsid
        queue.catalog_object(label, uid=str(uid))

    def purgeLabel(self, uid):
        """
        Remove a label from the queue
        """
        queue = self.getLabelQueue()
        queue.uncatalog_object(str(uid))

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
