from five import grok
import zope.component
from zope.app.intid.interfaces import IIntIds

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISpecimen
from avrc.data.store.interfaces import IAliquot

from hive.lab import utilities as utils
from hive.lab.interfaces.aliquot import IViewableAliquot
from hive.lab.interfaces.aliquot import IAliquotGenerator

from hive.lab.interfaces.specimen import IBlueprintForSpecimen

from hive.lab.interfaces.specimen import IViewableSpecimen
from hive.lab.interfaces.specimen import ISpecimenLabel
from hive.lab import MessageFactory as _

# @grok.adapter(IAliquot)
# @grok.implementer(ISpecimen)
# def SpecimenOfAliquot(context):
#     """ Translates an Aliquot into its parent Specimen
#     """
#     sm = zope.component.getSiteManager(self)
#     ds = sm.queryUtility(IDatastore, 'fia')
#     specimen_manager = ds.getSpecimenManager()
#     specimen = specimen_manager.get(context.specimen_dsid)
#     return specimen

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
    def special_instruction(self):
        return self.context.special_instruction

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