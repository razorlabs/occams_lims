from five import grok
import zope.component
from zope.app.intid.interfaces import IIntIds
import datetime, sys
from cStringIO import StringIO
from Products.ZCatalog.interfaces import ICatalogBrain 


from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISpecimen
from avrc.data.store.interfaces import IAliquot

from avrc.aeh.content.visit import IVisit
from avrc.aeh.content.patient import IPatient

from hive.lab import utilities as utils
from hive.lab.interfaces.aliquot import IViewableAliquot
from hive.lab.interfaces.aliquot import IAliquotGenerator

from hive.lab.interfaces.specimen import IBlueprintForSpecimen
from hive.lab.interfaces.labels import ILabelSheet
from hive.lab.interfaces.labels import ILabel
from hive.lab.interfaces.aliquot import IAliquotFilterForm

from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.interfaces.aliquot import IAliquotSupport
from hive.lab.interfaces.aliquot import IAliquotFilter
from hive.lab.interfaces.specimen import IViewableSpecimen
from hive.lab.interfaces.specimen import ISpecimenLabel
from hive.lab.content.factories import LabelGenerator
from hive.lab import MessageFactory as _


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
    def dsid(self):
        return self.context.dsid
        
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
    def pretty_aliquot_type(self):
        return self.context.type

    @property
    def notes(self):
        return self.context.notes
        
    @property
    def box(self):
        return self.context.box
        
    @property
    def volume(self):
        return self.context.volume

    @property
    def cell_amount(self):
        return self.context.cell_amount
        
    @property
    def store_date(self):
        return self.context.store_date
        
    @property
    def freezer(self):
        return self.context.freezer

    @property
    def rack(self):
        return self.context.rack

    @property
    def box(self):
        return self.context.box
        
    @property
    def state(self):
        return self.context.state
        
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
            date=self.context.date_collected.strftime("%m/%d/%Y")
        else:
            date=datetime.date.today().strftime("%m/%d/%Y")
        return date
            
    @property
    def barcodeline(self):
        return -1
        
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
            date=self.context.store_date.strftime("%m/%d/%Y")
        else:
            date=datetime.date.today().strftime("%m/%d/%Y")
        return date

    @property
    def label_lines(self):
        """
        Generate the lines for an Aliquot Label
        """
        ## Barcode Line
        line1 = unicode(self.dsid)
        line2 = unicode('%s OUR# %s ' %(self.dsid, self.patient_title))
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
        quelist=[]
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

class PatientAliquotFilter(grok.Adapter):
    """
    Filter Aliquot by Patient
    """
    grok.implements(IAliquotFilter)
    grok.context(IPatient)
        
    def getAliquotFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item based on an existing set of keys
        """
        intids = zope.component.getUtility(IIntIds)
        zid = intids.getId(self.context)
        retkw = {}
        for key in IAliquotFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all' or key == 'patient':
                    continue
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        retkw.update({'subject_zid':zid})
        return retkw
    

class VisitAliquotFilter(grok.Adapter):
    """
    Filter Aliquot by Patient
    """
    grok.implements(IAliquotFilter)
    grok.context(IVisit)
        
    def getAliquotFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item
        """
        intids = zope.component.getUtility(IIntIds)
        visit = self.context
        patient = visit.aq_parent
        patient_zid = intids.getId(patient)

        zidlist = []
        for cycle in visit.cycles:
            zidlist.append(cycle.to_id)
        retkw = {}
        for key in IAliquotFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all' or key == 'patient':
                    continue
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        retkw.update({'subject_zid':patient_zid, 'protocol_zid':zidlist})
        return retkw